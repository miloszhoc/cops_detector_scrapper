from typing import Dict

from playwright.sync_api import Page, Locator

from utils import websites_to_scap
from playwright._impl._errors import TimeoutError, Error


class BasePage():
    def __init__(self, page):
        super().__init__()
        self.page: Page = page

    def navigate(self, url):
        self.page.goto(url)

    def wait_for_page_to_load(self, timeout: float = 1000):
        self.page.wait_for_timeout(timeout)

    def scroll_down_page(self, count: int = 1):
        if isinstance(count, int):
            for i in range(count):
                self.page.keyboard.down('End')
        else:
            raise TypeError


class NieoznakowanyPage(BasePage):
    BUTTON_CLEAR_TABLE = "//button[@class='btn btn-outline-danger video-btn']"

    def click_clear_table_button(self):
        pass


class FacebookBasePage(BasePage):
    BASE_URL = websites_to_scap.Website.FACEBOOK.base_url

    @property
    def locators(self) -> Dict[str, Locator]:
        return {
            'ALLOW_ALL_COOKIES_MODAL_BUTTON': self.page.get_by_role("button", name="Zezwól na wszystkie pliki cookie"),
            'COOKIES_MODAL_TEXT': self.page.get_by_text(
                'Zezwolić na użycie plików cookie z Facebooka w tej przeglądarce?'),
            'BOTTOM_LOGIN_DIV_TEXT': self.page.get_by_text(
                'Zaloguj się lub zarejestruj na Facebooku, aby połączyć się ze znajomymi, członkami rodziny i osobami, które znasz.'),
            'LOGIN_OVERLAY_TEXT': self.page.locator('//span/span[contains(text(), "Wyświetl więcej na Facebooku")]'),
        }

    def __init__(self, page):
        super().__init__(page)
        # self.page.add_locator_handler(self.locators['COOKIES_MODAL_TEXT'], self.close_allow_all_files_modal)
        # self.page.add_locator_handler(self.locators['LOGIN_OVERLAY_TEXT'], self.remove_login_overlay)
        self.page.add_locator_handler(self.locators['BOTTOM_LOGIN_DIV_TEXT'], self.remove_login_bottom_div)

    def close_login_info_modal(self, timeout: int = 1000):
        self.page.get_by_label("Zamknij").click(timeout=timeout)

    def close_allow_all_files_modal(self):
        self.locators['ALLOW_ALL_COOKIES_MODAL_BUTTON'].click()

    def remove_login_bottom_div(self):
        self.page.evaluate(
            '''document.evaluate('//a[@aria-label="Utwórz nowe konto"]/../../../../../../div', document, null, XPathResult.ANY_TYPE, null).iterateNext().remove()''')

    def remove_login_overlay(self):
        # self.page.wait_for_timeout(1000)
        if self.locators['LOGIN_OVERLAY_TEXT'].is_visible():
            self.page.evaluate(
                '''document.evaluate('//div[contains(@class, "__fb-light-mode")][1]', document, null, XPathResult.ANY_TYPE, null).iterateNext().remove()''')


class FacebookGroupPage(FacebookBasePage):
    PHOTO_DETAILS_LINK = '//img[@alt and @height and @width]/../../../../parent::a[@role="link"]'

    def __init__(self, page, group_name):
        super().__init__(page)
        self.group_name = group_name
        self.navigate(f'{self.BASE_URL}/{self.group_name}/')

    def navigate_to_albums(self):
        self.page.goto(f'{self.BASE_URL}/{self.group_name}/photos_albums')
        return FacebookAlbumsPage(self.page)

    def open_first_photo_details(self):
        self.page.locator(self.PHOTO_DETAILS_LINK).element_handles()[0].click()
        return FacebookPhotoDetailsPage(self.page)

    def navigate_to_photos_page(self):
        self.page.goto(f'{self.BASE_URL}/{self.group_name}/photos')
        return FacebookPhotosPage(self.page)


class FacebookPhotosPage(FacebookBasePage):
    PHOTO_DETAILS_LINKS = '//img[@alt]/parent::a[@role="link"]'

    def open_first_photo_details(self):
        self.page.locator(self.PHOTO_DETAILS_LINKS).element_handles()[0].click()
        return FacebookPhotoDetailsPage(self.page)


class FacebookPhotosByPage(FacebookBasePage):
    PHOTO_DETAILS_LINKS = '//img[@alt]/parent::a[@role="link"]'

    def open_first_photo_details(self):
        self.page.locator(self.PHOTO_DETAILS_LINKS).element_handles()[0].click()
        return FacebookPhotoDetailsPage(self.page)


class FacebookAlbumsPage(FacebookBasePage):
    def get_album_names(self) -> list:
        albums = []
        for album in self.page.locator(
                '//a[@role="link"]//span[contains(text(), "")]/../../../../../parent::a').element_handles():
            album_name = album.inner_text().splitlines()[0]
            photo_number = album.inner_text().splitlines()[1]
            albums.append((album_name, photo_number))
        return albums

    def open_album_details(self, album_name: str):
        self.page.locator(f'//span[contains(text(), "{album_name}")]').click(timeout=3000)
        self.wait_for_page_to_load(4000)
        return FacebookAlbumDetailsPage(self.page)


class FacebookAlbumDetailsPage(FacebookBasePage):
    def open_first_photo_in_album(self):
        try:
            print(self.page.url)
            self.page.locator('//a[@aria-label="Zdjęcie w albumie" and @role="link"]').element_handles()[0].click()
        except IndexError:
            self.page.locator('//img/parent::a/parent::div').element_handles()[0].click()
        return FacebookPhotoDetailsPage(self.page)


class FacebookPhotoDetailsPage(FacebookBasePage):
    IMAGE_LOCATOR = '//div[@aria-label="Przeglądarka zdjęć"]//img[@data-visualcompletion="media-vc-image"]'
    ALT_IMAGE_LOCATOR = '//img[@data-visualcompletion="media-vc-image"]'

    # @property
    # def locators(self) -> Dict[str, Locator]:
    #                 'DESCRIPTION_DATE_HOVER_LINK': }
    #     print('DEBUG', len(_locators))
    #     return super().locators.update(_locators)

    def hover_over_photo(self):
        try:
            self.page.get_by_role("img", name="Brak dostępnego opisu zdjęcia.").hover(timeout=1000)
        except (TimeoutError, Error):
            try:
                self.page.locator(self.IMAGE_LOCATOR).hover(timeout=1000)
            except TimeoutError:
                self.page.locator(self.ALT_IMAGE_LOCATOR).hover(timeout=1000)

    def next_photo_button_is_visible(self):
        self.hover_over_photo()
        return self.page.get_by_label("Następne zdjęcie").is_visible()

    def show_more_button_is_visible(self):
        return self.page.get_by_role("complementary").get_by_text("Wyświetl Więcej", exact=True)

    def click_first_show_more_button(self):
        # show_more_buttons = self.page.get_by_role("complementary").get_by_role("button", name="Wyświetl Więcej").element_handles()
        # show_more_buttons = self.page.get_by_role("complementary").get_by_text("Wyświetl Więcej").element_handles()
        # show_more_buttons = self.page.get_by_role("button").and_(self.page.get_by_text("Wyświetl Więcej", exact=True))
        show_more_buttons = self.page.get_by_text("Wyświetl więcej", exact=True).element_handles()
        for button in show_more_buttons:
            button.click()


    def get_photo_description(self):
        """
        :return: Photo description if exists, else return NO_PHOTO_DESCRIPTION
        """
        try:
            photo_description = self.page.locator(
                '//a[contains(@href, "hashtag")]/../parent::span[@dir="auto"]').inner_text(timeout=2000)
        except TimeoutError:
            photo_description = 'NO_PHOTO_DESCRIPTION'
        return photo_description

    def get_image_url(self):
        try:
            img_url = self.page.locator(self.IMAGE_LOCATOR).element_handles()[0].get_attribute('src')
        except Exception as e:
            img_url = 'NO_URL'
            print(e)
        return img_url

    def click_next_picture(self, timeout: float = 3000):
        self.hover_over_photo()
        self.page.get_by_label("Następne zdjęcie").click(timeout=timeout)

    def expand_photo_description(self):
        try:
            self.click_first_show_more_button()
        except (TimeoutError, IndexError):
            print('No expandable description, skipping...')

    def get_date_of_the_picture(self):
        date = None
        try:
            self.page.locator('//*[@role="complementary"]//span/*/a[@role="link" and contains(@href, "/posts/")]').element_handles()[0].hover()
        except IndexError:
            self.page.locator('//*[@role="complementary"]//span/*/a[@role="link" and contains(@href, "/photo/")]').element_handles()[0].hover()
        date = self.page.locator('//div[@role="tooltip"]/span').inner_text()
        return date
