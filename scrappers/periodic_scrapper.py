import json
import sys

from playwright.sync_api import sync_playwright, Error

from env_config.config import BUCKET_NAME, TEST_DATA_ROOT_FOLDER, PROJECT_ROOT_FOLDER
from scrappers.pom.api_calls import ApiConnector
from utils.utils import parse_polish_datetime, add_timestamp, get_today_date, upload_to_s3

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
    periodic_data = []
    test_data_folder = f'{TEST_DATA_ROOT_FOLDER}/periodic_update/{group_name}'
    with (sync_playwright() as playwright):
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context(viewport={"height": 720, "width": 1280})
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
        page = context.new_page()

        # go to facebook group page, navigate to albums and close all popups/modals
        fb_page = FacebookGroupPage(page, group_name)
        photos_page = fb_page.navigate_to_photos_page()

        with open(f'{test_data_folder}/last_added.txt', 'r') as f:
            last_added = f.read()

        photos_page.wait_for_page_to_load(2000)
        photos_page.close_allow_all_files_modal()
        photos_page.remove_login_overlay()
        photo_details_page = photos_page.open_first_photo_details()
        current_picture_iter = 0
        while True:
            record = {}
            photo_details_page.wait_for_page_to_load(3000)
            photo_details_page.remove_login_overlay()
            photo_details_page.wait_for_page_to_load(2000)
            photo_details_page.scroll_down_page(2)

            photo_details_page.expand_photo_description()
            photo_description = photo_details_page.get_photo_description()
            photo_details_page.wait_for_page_to_load(1000)
            date = photo_details_page.get_date_of_the_picture()
            parsed_date = parse_polish_datetime(date)

            if last_added == parsed_date:
                break

            img_url = photo_details_page.get_image_url()
            filename = add_timestamp('picture')
            try:
                filepath = ApiConnector(context.request).download_image(img_url,
                                                                        f'{test_data_folder}/pictures/{filename}')
                filepath = str(filepath.absolute())
                s3_file_path = upload_to_s3(filepath, BUCKET_NAME, f'pictures/{group_name}/{filename}')
            except (Error, AttributeError) as e:
                filepath = 'COULD NOT DOWNLOAD FILE'
                s3_file_path = 'COULD NOT DOWNLOAD FILE'
                print(e)
            record['description'] = photo_description
            record['img_url'] = img_url
            record['img_path'] = filepath  # local path
            record['s3_path'] = s3_file_path
            record['source'] = group_name
            record['date'] = parsed_date
            periodic_data.append(record)

            if current_picture_iter == 0:
                with open(f'{test_data_folder}/last_added.txt', 'w+') as f:
                    f.write(parsed_date)

            photo_details_page.click_next_picture()
            current_picture_iter += 1
        context.tracing.stop(path="trace.zip")
        context.close()

    today_date = get_today_date()
    with open(f'{test_data_folder}/periodic.json', 'w+') as f:
        json.dump(periodic_data, f, ensure_ascii=False)
        remote_file_path = f'{today_date}/{group_name}/periodic.json'
    upload_to_s3(f.name, BUCKET_NAME, remote_file_path)


if __name__ == '__main__':
    get_data_from_group_board('nieoznakowaneradiowozy')
