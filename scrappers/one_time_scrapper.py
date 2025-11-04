import sys

sys.path.append('/Users/milosz/PycharmProjects/cops_detector', )
# sys.path.append('/Users/milosz/PycharmProjects/cops_detector/scrappers/pom',)

from playwright.sync_api import sync_playwright
from playwright._impl._errors import TimeoutError, Error
from scrappers.pom.api_calls import ApiConnector
from scrappers.pom.pages import NieoznakowanyPage, FacebookGroupPage
from utils.voivodeships import Voivodeship
from utils.websites_to_scap import Website
from utils.utils import extract_data_from_urls, add_timestamp


def get_data_from_nieoznakowany_pl():  # todo finish - save to db
    base_url = Website.NIEOZNAKOWANY.base_url
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        current_page = NieoznakowanyPage(page)
        urls = []
        for data in Voivodeship:
            print(f'checking {data.readable_name}')
            current_page.navigate(f'{base_url}/public/index.php?name=list&country={data.readable_name}&back=1')
            page.on('request', lambda request: urls.append(request.url) if 'change.php?' in request.url else '')
        car_data = extract_data_from_urls(urls)
        browser.close()


def get_data_from_facebook_group_albums(group_name: str, excluded_albums: list, included_albums: list = ()):
    '''
    1. Open facebook group
    2. Go to group albums page.
    3. Get all albums names (omit given albums)
    4. For each album:
        a) open album details
        b) open first photo in album
        c) expand photo description if possible
        d) get photo description
        e) get image url
        f) download picture
        g) go to next picture

        If no more pictures in album, navigate to group albums page and open next album.

    :param group_name: facebook group name
    :param excluded_albums: name of the albums to be excluded
    :param included_albums: albums to be included (if empty, script will get list of albums by itself)
    :return:
    '''
    with (sync_playwright() as playwright):
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        # context.tracing.start(screenshots=True, snapshots=True, sources=True)
        page = context.new_page()

        # go to facebook group page, navigate to albums and close all popups/modals
        fb_page = FacebookGroupPage(page, group_name)
        fb_albums_page = fb_page.navigate_to_albums()
        fb_albums_page.close_allow_all_files_modal()
        fb_albums_page.close_login_info_modal()

        # scroll down page to load more albums, and wait for the albums to load (hard wait)
        fb_albums_page.scroll_down_page(3)
        fb_albums_page.wait_for_page_to_load(2000)

        # get all album names that are in facebook group
        if included_albums:
            albums_to_scrap = included_albums
        else:
            albums_to_scrap = fb_albums_page.get_album_names()

        print(albums_to_scrap)
        # exclude albums
        for album in reversed(albums_to_scrap):
            if album[0] in excluded_albums:
                albums_to_scrap.remove(album)

        for album, number_of_pic in albums_to_scrap:
            fb_albums_page.scroll_down_page(3)
            album_details_page = fb_albums_page.open_album_details(album)
            try:
                album_details_page.close_login_info_modal()
            except:
                pass
            fb_albums_page.scroll_down_page(2)
            fb_albums_page.wait_for_page_to_load(1500)

            photo_details_page = album_details_page.open_first_photo_in_album()

            photo_details_page.wait_for_page_to_load()
            i = 0
            photo_details_page.remove_login_bottom_div()
            while True:
                try:
                    photo_details_page.close_login_info_modal(timeout=100)
                except:
                    pass
                photo_details_page.expand_photo_description()
                with open(f'../test_data/group_photos/cars_{album}', 'a+') as f:
                    photo_description = photo_details_page.get_photo_description()
                    img_url = photo_details_page.get_image_url()
                    filename = add_timestamp('picture')
                    try:
                        filepath = ApiConnector(context.request).download_image(img_url,
                                                                                f'../test_data/group_photos/pictures/{filename}')
                        filepath = filepath.absolute()
                    except (Error, AttributeError):
                        filepath = 'COULD NOT DOWNLOAD FILE'
                    f.write(
                        f'''DESCRIPTION: {photo_description} \nIMG_URL: {img_url} \nIMG_PATH: {filepath}  \n\n-------------\n\n''')
                i += 1
                print(f'{album} ({number_of_pic}) - {i}')
                try:
                    photo_details_page.wait_for_page_to_load()
                    photo_details_page.click_next_picture()
                    photo_details_page.remove_login_overlay()
                except TimeoutError:
                    fb_page.navigate_to_albums()
                    fb_page.close_login_info_modal()
                    break
            page.wait_for_timeout(5000)
        # context.tracing.stop(path="trace.zip")
        context.close()


get_data_from_facebook_group_albums('nieoznakowaneradiowozy',
                                    ['Like it ;)', 'Zdjęcia w tle', 'Zdjęcia profilowe'],
                                    included_albums=[('Woj. Podlaskie', '117'),
                                                     ('Woj. Małopolskie', '124'),
                                                     ('Woj. Mazowieckie', '196'),])

# ('Woj. Śląskie', '114'),
# ('Woj.Świętokrzyskie', '140'),
# ('Woj. Wielkopolskie', '84'),
# ('Woj. Podkarpackie', '109'),

# ('Woj. Podlaskie', '117'),
# ('Woj. Małopolskie', '124'),
# ('Woj. Mazowieckie', '196'),
