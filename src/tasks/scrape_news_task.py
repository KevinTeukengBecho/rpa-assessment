from robocorp.tasks import task
from RPA.Browser.Selenium import Selenium

from src.business_logic.scrape_la_times_news import ScrapeLaTimesNews

browser = Selenium()

search_term = "trump"
search_category = "Politics"
browser_url = "https://www.latimes.com/"
number_of_month = 2
output_path = "output"


@task
def search_news():
    ScrapeLaTimesNews(
        browser=browser,
        search_phrase=search_term,
        category=search_category,
        number_of_months=number_of_month,
        news_url=browser_url,
        output_path=output_path,
    ).scrape()
