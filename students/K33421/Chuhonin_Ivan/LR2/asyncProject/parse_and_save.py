import requests
from bs4 import BeautifulSoup

from db import create_rec

headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36'}


def parse_and_save(param: tuple[str, str]):
    url = param[0]
    dbname = param[1]

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')
    data = soup.find('h1').string

    create_rec(data, dbname)


# async part
async def parse_and_save_async(url):
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')
    data = soup.find('h1').string
    return data
