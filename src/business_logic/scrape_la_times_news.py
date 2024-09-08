import logging
import time
from datetime import date, datetime

from selenium.webdriver.common.keys import Keys

from src.business_logic.scrape_news import ScrapeNews
from src.business_logic.scrape_utils import download_image, sanitize_string
from src.dtos.news_item_dto import NewsItemDto
from src.exceptions.exceptions import (
    NewsCategoryNotFoundException,
    ParseNewsDateException,
    SearchPhraseContainsNoResultsException, UnexpectedEndOfNavigation,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScrapeLaTimesNews(ScrapeNews):
    def enter_search_phrase(self):
        """Specify and search for the search_phrase."""
        search_button_xpath = "xpath://header//button[@data-element='search-button']"
        input_xpath = "xpath://input[@data-element='search-form-input']"

        self.browser.click_element_when_visible(search_button_xpath)
        self.browser.input_text(input_xpath, self.search_phrase)
        self.browser.press_keys(input_xpath, Keys.RETURN)
        logger.info(
            "Successfully submitted a search for phrase '%s'", self.search_phrase
        )

    def verify_search_results(self):
        """Verify the search returned any results

        Throws: SearchPhraseContainsNoResultsException if search does not contain any results
        """
        news_results_item_xpath = "xpath://ps-promo"

        try:
            self.browser.wait_until_element_is_visible(
                news_results_item_xpath, timeout=15
            )
            logger.debug("Search phrase '%s' contains results.", self.search_phrase)
        except AssertionError:
            raise SearchPhraseContainsNoResultsException(
                f"Search phrase '{self.search_phrase}' does not contain any results"
            )

    def select_category_if_exists(self):
        """Select the category if it exists for the news website."""
        see_all_text_selector = "xpath://span[text()='See All']"
        category_selector = (
            f"xpath://label[span[text()='{self.category}']]/input[@type='checkbox']"
        )

        logger.info("Looking for news category %s", self.category)
        try:
            self.browser.click_element_when_visible(see_all_text_selector)
            self.browser.wait_until_element_is_visible(category_selector, timeout=15)
            self.browser.click_element_when_visible(category_selector)
            logger.info("Successfully selected news category %s", self.category)
        except AssertionError:
            raise NewsCategoryNotFoundException(
                f"News category '{self.category}' does not exist"
            )

    def sort_search_results_by_latest(self):
        select_locator = "css:select.select-input[name='s']"
        self.browser.select_from_list_by_label(select_locator, "Newest")

    def extract_news_items(self):
        news_results_item_xpath = "xpath://ps-promo"

        try:
            self.browser.wait_until_element_is_visible(
                news_results_item_xpath, timeout=15
            )
            list_items = self.browser.get_webelements(news_results_item_xpath)
        except AssertionError:
            raise SearchPhraseContainsNoResultsException(
                f"Search phrase '{self.search_phrase}' does not contain any results"
            )

        for idx, item in enumerate(list_items):
            try:
                logger.info("processing item number %s", idx)
                # self.browser.wait_until_element_is_visible(item)
                self.browser.scroll_element_into_view(item)
                module_id = self.browser.get_element_attribute(item, "data-module-id")
                logger.info("module id is %s", module_id)
                title = self.browser.get_text(
                    f"xpath://ps-promo[@data-module-id='{module_id}']//h3[@class='promo-title']"
                )
                logger.info("title is %s", title)
                description = self.browser.get_text(
                    f"xpath://ps-promo[@data-module-id='{module_id}']//p[@class='promo-description']"
                )
                logger.info("description is %s", description)
                news_date_text = self.browser.get_text(
                    f"xpath://ps-promo[@data-module-id='{module_id}']//p[contains(@class, 'promo-timestamp')]"
                )

                image_element = self.browser.find_element(
                    f"xpath://ps-promo[@data-module-id='{module_id}']//div[@class='promo-media']/a/picture/img"
                )
                image_url = self.browser.get_element_attribute(image_element, "src")
                image_name = download_image(
                    image_url, f"{self.output_path}/images", f"{sanitize_string(title)}.jpg"
                )

                news_date = self._process_la_times_news_date(news_date_text)
                current_date = datetime.now().date()
                logger.info("Extracted all information")
                retry_processing = 5

                if current_date.year == news_date.year and (
                    current_date.month - news_date.month
                ) <= (self.number_of_months - 1):
                    self.news_items.append(
                        NewsItemDto(
                            title=title,
                            description=description,
                            date=news_date,
                            image_name=image_name,
                        )
                    )
                else:
                    self.can_navigate_to_next_page = False
            except Exception:
                time.sleep(30)
                # Process the next news item if the current one fails for some unexpected reason.
                logger.exception("An error occurred when processing a news item.")
                break

    @staticmethod
    def _process_la_times_news_date(value: str) -> date:
        if "ago" in value:
            return date.today()
        try:
            month = value[:3]
            value_split = value.split(",")
            year = value_split[1].strip()
            day = int(value_split[0][4:].strip())
            current_info_date = datetime.strptime(f"{day} {month} {year}", "%d %b %Y")
            return current_info_date.date()
        except Exception:
            raise ParseNewsDateException(f"Failed to parse date {value}")

    def navigate_to_next_page(self):
        next_element_locator = (
            "xpath://div[@class='search-results-module-next-page']//a"
        )
        try:
            self.browser.click_element_when_visible(next_element_locator)
        except AssertionError:
            raise UnexpectedEndOfNavigation("Unable to navigate to the next page. we probably reached the end of results")
