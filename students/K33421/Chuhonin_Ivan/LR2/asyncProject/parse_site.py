from typing import List
import requests
from bs4 import BeautifulSoup

from parse_and_save import headers


def get_sources() -> List[str]:
    result = []
    urls = ['https://opticdevices.ru/category_27.html',
            'https://opticdevices.ru/category_27_offset_12.html',
            'https://opticdevices.ru/category_27_offset_24.html']
    for url in urls:
        print(url)
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        links = soup.find_all('a', href=lambda href: href and 'product' in href)
        for link in {link['href'] for link in links}:
            result.append(link)

    return result
