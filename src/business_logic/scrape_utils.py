import os
import re

import requests
from RPA.Excel.Files import Files

from src.dtos.news_item_dto import NewsItemDto


def download_image(image_url: str, image_folder_path: str, image_name) -> str:
    """Downloads an image and save it to a specified folder and return the image file name"""
    os.makedirs(image_folder_path, exist_ok=True)
    image_response = requests.get(image_url)
    counter = 1
    image_file_path = ""

    if image_response.status_code == 200:
        image_file_path = f"{image_folder_path}/{image_name}"

        while os.path.exists(image_file_path):
            image_file_path = f"{image_file_path}_{counter}"
            counter += 1

        image_data = image_response.content
        with open(image_file_path, "wb") as image_file:
            image_file.write(image_data)

    return image_file_path


def sanitize_string(value: str) -> str:
    """Sanitize a string and remove all special characters"""
    return re.sub(r"[^A-Za-z0-9 ]+", "", value).replace(" ", "").strip()


def save_news_to_excel(
    file_name: str, file_path: str, news_items: list[NewsItemDto], search_phrase: str
):
    os.makedirs(file_path, exist_ok=True)
    excel = Files()
    excel.create_workbook()
    excel_data = []
    header_data = [
        "title",
        "date",
        "description",
        "picture filename",
        "count of search phrase",
        "News contains money",
    ]
    excel_data.append(header_data)

    for news_item in news_items:
        excel_data.append(
            [
                news_item.title,
                news_item.date,
                news_item.description,
                news_item.image_name,
                news_item.phrase_count_in_title_and_description(search_phrase),
                news_item.title_or_description_contains_money(),
            ]
        )

    for row_index, row_data in enumerate(excel_data):
        for col_index, value in enumerate(row_data, start=1):
            excel.set_cell_value(row_index + 1, col_index, value)

    excel.save_workbook(f"{file_path}/{file_name}")
    excel.close_workbook()
