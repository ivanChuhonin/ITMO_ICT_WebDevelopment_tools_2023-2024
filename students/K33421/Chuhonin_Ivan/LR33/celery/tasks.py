from bs4 import BeautifulSoup
from celery import Celery
import requests
from typing import List, Optional
from urllib.parse import urlparse, urljoin, urlunparse


headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36'}


celery = Celery(__name__,
                broker='redis://redis:6379/0',
                backend='db+postgresql+psycopg2://pguser:pgpwd123@db:5432/celery_parser')


@celery.task(name='parser')
def parser(url: str):
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')
    return soup.find('h1').string.strip('"')


@celery.task(name='catalog')
def catalog(url: str) -> List[str]:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')

    links = soup.find_all('a', href=lambda href: href and 'product' in href)
    parsed_url = urlparse(url)
    scheme = parsed_url.scheme
    host = parsed_url.netloc
    result = []
    for link in {link['href'] for link in links}:
        result.append(urlunparse((scheme, host, link, "", "", "")))

    return result


# urls = ['https://opticdevices.ru/category_27.html',
#         'https://opticdevices.ru/category_27_offset_12.html',
#         'https://opticdevices.ru/category_27_offset_24.html']
