# Лабораторная работа №3

## Цель лабораторной работы

Научиться упаковывать FastAPI приложение в Docker, интегрировать парсер данных с базой данных и вызывать парсер через API и очередь.

## Описание работы

* Задача - Упаковка FastAPI приложения, базы данных и парсера данных в Docker

* Вызов парсера из FastAPI

* Вызов парсера из FastAPI через очередь


## Реализация

### `Dockerfile`
```
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
```

### `main.py`
```
from fastapi import FastAPI
from tasks import parser, catalog
from celery.result import AsyncResult

app = FastAPI()

@app.post("/parser/")
async def create_task(url: str):
    task = parser.delay(url)
    return {"task_id": task.id}


@app.post("/catalog/")
async def create_task(url: str):
    task = catalog.delay(url)
    return {"task_id": task.id}


@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    task_result = AsyncResult(task_id)
    result = {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result
    }
    return result
```

### `task.py`
```
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
```

## Вывод
В данной лабораторной работе были получены навыки по упаковке Fastapi приложения в Docker, а также по использованию Celery и Redis для организации очередей при решении задачи парсинга.