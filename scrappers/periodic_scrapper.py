import json
import sys

from playwright.sync_api import sync_playwright, Error

from lambda_function.lambda_function import upload_file_to_s3
from s3_uploader import BUCKET_NAME
from scrappers.pom.api_calls import ApiConnector
from utils.utils import parse_polish_datetime, add_timestamp

sys.path.append('/Users/milosz/PycharmProjects/cops_detector', )

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
    root_folder = '/Users/milosz/PycharmProjects/cops_detector/test_data/periodic_update'
    with (sync_playwright() as playwright):
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context(viewport={"height": 720, "width": 1280})
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
        page = context.new_page()

        # go to facebook group page, navigate to albums and close all popups/modals
        fb_page = FacebookGroupPage(page, group_name)
        photos_page = fb_page.navigate_to_photos_page()

        with open(f'{root_folder}/last_added.txt', 'r') as f:
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
            # print(date, parsed_date)

            if last_added == parsed_date:
                break

            img_url = photo_details_page.get_image_url()
            filename = add_timestamp('picture')
            try:
                filepath = ApiConnector(context.request).download_image(img_url,
                                                                        f'../test_data/periodic_update/pictures/{filename}')
                filepath = str(filepath.absolute())
                s3_file_path = upload_file_to_s3(BUCKET_NAME, filepath)
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
                with open(f'{root_folder}/last_added.txt', 'w+') as f:
                    f.write(parsed_date)

            photo_details_page.click_next_picture()
            current_picture_iter += 1

        with open(f'{root_folder}/periodic.json', 'w+') as f:
            json.dump(periodic_data, f, ensure_ascii=False)

        context.tracing.stop(path="trace.zip")

        # with open(f'../test_data/group_photos/cars_{album}', 'a+') as f:
        #     photo_description = photo_details_page.get_photo_description()
        #     img_url = photo_details_page.get_image_url()
        #     filename = add_timestamp('picture')
        #     try:
        #         filepath = ApiConnector(context.request).download_image(img_url,
        #                                                                 f'../test_data/group_photos/pictures/{filename}')
        #         filepath = filepath.absolute()
        #     except (Error, AttributeError):
        #         filepath = 'COULD NOT DOWNLOAD FILE'
        #     f.write(
        #         f'''DESCRIPTION: {photo_description} \nIMG_URL: {img_url} \nIMG_PATH: {filepath}  \n\n-------------\n\n''')
        # i += 1
        # print(f'{album} ({number_of_pic}) - {i}')
        # photo_details_page.wait_for_page_to_load(timeout=3000)
        # i += 1
        # if i == 10:
        #     break
        # page.wait_for_timeout(5000)
    # context.close()


# with (sync_playwright() as playwright):
#     browser = playwright.chromium.launch(headless=True)
#     context = browser.new_context()
#     page = context.new_page()
#
#     go to facebook group page, and close all popups/modals
# fb_page = FacebookGroupPage(page, group_name)
# photos_by_page = fb_page.navigate_to_photos_by_page()
#
# photos_by_page.close_allow_all_files_modal()
# photos_by_page.close_login_info_modal()
#
# photos_by_page.wait_for_page_to_load(3000)
# photo_details_page = photos_by_page.open_first_photo_details()
# photo_details_page.wait_for_page_to_load()
#
# i = 0
# photo_details_page.remove_login_bottom_div()
# while True:
#     try:
#         if photo_details_page.show_more_button_is_visible():
#             photo_details_page.click_first_show_more_button()
#             photo_details_page.wait_for_page_to_load(300)
#     except (TimeoutError, Error, IndexError):
#         pass
#     with open(f'../test_data/periodic_update/update', 'a+') as f:
#         try:
#             photo_description = photo_details_page.get_photo_description()
#         except TimeoutError:
#             photo_description = 'NO_PHOTO_DESCRIPTION'
#         try:
#             img_url = photo_details_page.get_image_url()
#         except:
#             img_url = 'NO_URL'
#         f.write(f'''DESCRIPTION: {photo_description} \nIMG_URL: {img_url} \n\n-------------\n\n''')
#     i += 1
#     print(f'{album} ({number_of_pic}) - {i}')
#
#
#
#
#
# try:
#     photo_details_page.wait_for_page_to_load()
#     photo_details_page.click_next_picture()
# except TimeoutError:
#     break
# page.wait_for_timeout(5000)
# context.close()


get_data_from_group_board('nieoznakowaneradiowozy')
