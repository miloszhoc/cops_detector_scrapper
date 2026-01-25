import json
import sys

from playwright.sync_api import sync_playwright, Error

from env_config.config import BUCKET_NAME, TEST_DATA_ROOT_FOLDER, PROJECT_ROOT_FOLDER
from scrappers.pom.api_calls import ApiConnector
from utils.logs import LOGGER
from utils.utils import parse_polish_datetime, add_timestamp, get_today_date, upload_to_s3, get_file_content_from_s3

sys.path.append(PROJECT_ROOT_FOLDER, )

from scrappers.pom.pages import FacebookGroupPage


def get_data_from_group_board(group_name: str):
    """
    1. Open facebook group
    2. Navigate to "photos_by" page
    3. Close popups and modals
    4. Open first photo
    4. For each album:
        a) open album details
        b) open first photo in album
        c) expand photo description if possible
        d) get photo description
        e) get image url
        f) download picture
        g) go to next picture

    :return:
    """
    today_date = get_today_date()
    LOGGER.info(f'today_date: {today_date}')
    periodic_data = []
    test_data_folder = f'{TEST_DATA_ROOT_FOLDER}/periodic_update/{group_name}'
    LOGGER.info(f'test_data_folder: {test_data_folder}')
    with (sync_playwright() as playwright):
        LOGGER.info("Starting Playwright...")
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(viewport={"height": 720, "width": 1280},
                                      locale='pl-PL',
                                      timezone_id='Europe/Warsaw')
        # context.tracing.start(screenshots=True, snapshots=True, sources=True)
        page = context.new_page()

        # go to facebook group page, navigate to albums and close all popups/modals
        fb_page = FacebookGroupPage(page, group_name)
        photos_page = fb_page.navigate_to_photos_page()
        LOGGER.info(f'Navigated to photos page (group_name/photos)...')

        last_added = get_file_content_from_s3(f'processing_dates/{group_name}/last_added.txt')
        LOGGER.info("Last added picture date: {}".format(last_added))

        photos_page.wait_for_page_to_load(2000)
        photos_page.close_allow_all_files_modal()
        photos_page.remove_login_overlay()
        LOGGER.info('Started processing...')
        photo_details_page = photos_page.open_first_photo_details()
        LOGGER.info('Opened first picture...')
        current_picture_iter = 0
        while True:
            LOGGER.info(f'Current picture ({str(current_picture_iter)}) URL: {photos_page.page.url}')
            record = {}
            photo_details_page.wait_for_page_to_load(3000)
            photo_details_page.remove_login_overlay()
            photo_details_page.wait_for_page_to_load(2000)
            photo_details_page.scroll_down_page(2)

            photo_details_page.expand_photo_description()
            LOGGER.info('Expanded photo description')
            photo_description = photo_details_page.get_photo_description()
            LOGGER.info('Photo description: {}'.format(photo_description))
            photo_details_page.wait_for_page_to_load(1000)
            date = photo_details_page.get_date_of_the_picture()
            parsed_date = parse_polish_datetime(date)
            LOGGER.info(f'Photo date: {date} (parsed date: {parsed_date})')
            if last_added == parsed_date:
                LOGGER.info('Item already processed, skipping...')
                break

            img_url = photo_details_page.get_image_url()
            LOGGER.debug(f'img_url: {img_url}')
            filename = add_timestamp('picture')
            try:
                filepath = ApiConnector(context.request).download_image(img_url,
                                                                        f'{test_data_folder}/pictures/{filename}')
                filepath = str(filepath.absolute())
                LOGGER.info(f'Photo filepath: {filepath}')
                s3_file_path = upload_to_s3(filepath, BUCKET_NAME, f'pictures/{group_name}/{filename}')
                LOGGER.info(f'S3 file path: {filepath}')
            except (Error, AttributeError) as e:
                filepath = 'COULD NOT DOWNLOAD FILE'
                s3_file_path = 'COULD NOT DOWNLOAD FILE'
                LOGGER.error(e)
                LOGGER.error(f'ERROR while processing: filepath: {filepath}, s3_file_path: {s3_file_path}')
            record['description'] = photo_description
            record['img_url'] = img_url
            record['img_path'] = filepath  # local path
            record['s3_path'] = s3_file_path
            record['source'] = group_name
            record['date'] = parsed_date
            periodic_data.append(record)
            LOGGER.info(f'Record has been added to the list: {record}')

            if current_picture_iter == 0:
                last_added_local_path = f'{test_data_folder}/last_added.txt'
                with open(last_added_local_path, 'w+') as f:
                    f.write(parsed_date)
                    LOGGER.info(f'Updated last added picture date: {parsed_date}')
                upload_to_s3(last_added_local_path, BUCKET_NAME, f'processing_dates/{group_name}/last_added.txt')
                LOGGER.info(f'Uploaded last added picture date to S3 ({BUCKET_NAME}): {parsed_date}')

            with open(f'{test_data_folder}/periodic.json', 'w+') as f:
                json.dump(periodic_data, f, ensure_ascii=False)
                remote_file_path = f'{today_date}/{group_name}/periodic.json'

            photo_details_page.click_next_picture()
            current_picture_iter += 1
            LOGGER.info(f'Moved to the next picture...')
        # context.tracing.stop(path="trace.zip")
        context.close()
        LOGGER.info('Processing completed...')
    upload_to_s3(f.name, BUCKET_NAME, remote_file_path)
    LOGGER.info('Uploaded picture records data to S3.')
