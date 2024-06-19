import json  #для создания json файла с результатами парсинга
import os  #для выбора/создания папки, куда будет сохранять результаты
import sys  #для проверки вводимых данных
import logging
import requests  #для запросов и получения ответов на сайте
import bs4  #для конвертации ответов и работе с ними
from bs4 import BeautifulSoup
from datetime import datetime  #для обработки даты публикации
from typing import Union  #также будем использовать для обработки даты публикации
from fake_useragent import UserAgent  #для динамического useragent, хотя можно использовать дефолтный

DOMEN = 'https://www.okx.com/'  #определяем домен для дальнейшего формирования ссылок
BASE_URL = 'https://www.okx.com/help/section'  #определяем url на основе которого будут формироваться ссылки с секциями + новостями
ua = UserAgent()
HEADERS = {
    'User-Agent': ua.chrome
}

SECTIONS = [
    'announcements-latest-announcements',
    'announcements-latest-events',
    'announcements-deposit-withdrawal-suspension-resumption',
    'announcements-spot-margin-trading',
    'announcements-derivatives',
    'announcements-oktc',
    'announcements-fiat-gateway',
    'announcements-okx-broker',
    'announcements-okx-pool-announcement',
    'announcements-new-token',
    'announcements-introduction-to-digital-assets',
    'announcements-okb-buy-back-burn',
    'announcements-api',
    'announcements-others',
    'announcements-product-updates',
    'announcements-web3'
]


def create_folder(folder_path):  #функция для создания/выбора папки для сохранения результатов
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)


def create_json(data, file_path):  #функция для создания json файла с результатами
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def get_page_url(section: str, page_number: int = 1) -> str:  #функция для формирования ссылки на страницу в секции
    return f'{BASE_URL}/{section}/page/{page_number}'


def get_soup(url: str) -> BeautifulSoup:  #функция для формирования запроса и создания объекта bs для парсинга
    response = requests.get(url=url, headers=HEADERS)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup
    else:
        logging.critical(f'Something went wrong with requesting {url}\nStatus code: {response.status_code}')


def get_last_page_number(soup: BeautifulSoup) -> int:  #функция для получения номера последней страницы
    last_page_number = soup.find_all('a', {'class': 'okui-pagination-item okui-pagination-item-link'})
    if last_page_number:
        return int(last_page_number[-1].text)
    else:
        return 1


def get_articles_info_from_page(soup: bs4.BeautifulSoup,
                                start_date: Union[str, datetime],
                                end_date: Union[str, datetime]) -> list:  #функция для получения основной информации по статьям
    if not isinstance(start_date, datetime):
        start_date = datetime.strptime(start_date, '%Y-%m-%d')

    if not isinstance(end_date, datetime):
        end_date = datetime.strptime(end_date, '%Y-%m-%d')

    li_soup = soup.find_all('li', {'class': 'index_article__15dX1'})
    articles_info = []

    for i in li_soup:
        article_date_str = i.find('span').text.strip('Published on')
        article_datetime = datetime.strptime(article_date_str, '%b %d, %Y')

        if article_datetime >= start_date and article_datetime <= end_date:
            article_link = DOMEN.rstrip('/') + i.find('a')['href']
            article_title = i.find('div', {'class': 'index_title__6wUnB'}).text.strip()
            article_info = {
                'title': article_title,
                'date': article_datetime.strftime('%Y-%m-%d'),
                'link': article_link
            }
            articles_info.append(article_info)

    return articles_info


def execute(start_date, end_date, folder):  #результирующая функция которая парсит данные
    create_folder(folder)
    all_articles_info = []

    for section in SECTIONS:
        start_url = get_page_url(section)
        soup = get_soup(start_url)

        if soup:
            pages = get_last_page_number(soup)

            for page in range(1, pages + 1):
                url = get_page_url(section, page_number=page)
                soup = get_soup(url)

                if soup:
                    articles_info = get_articles_info_from_page(soup, start_date, end_date)
                    all_articles_info.extend(articles_info)

    json_file_path = os.path.join(folder, 'articles_info.json')
    create_json(all_articles_info, json_file_path)
    print(f'json file saved in: {json_file_path}')


if __name__ == '__main__':
    start_date = sys.argv[1]  #первый объект в командной строке будет датой от которой будем производить парсинг
    end_date = sys.argv[2]  #второй объект в командной строке будет датой до которой будем производить парсинг
    folder = sys.argv[3]  #третий объект в командной строке будет путем к папке куда будут сохраняться результаты парсинга

    execute(start_date, end_date, folder)
