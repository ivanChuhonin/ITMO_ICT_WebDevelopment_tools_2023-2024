# Лабораторная работа №3

## Цель лабораторной работы

Научиться упаковывать FastAPI приложение в Docker, интегрировать парсер данных с базой данных и вызывать парсер через API и очередь.

## Описание работы

* Задача - Упаковка FastAPI приложения, базы данных и парсера данных в Docker

* Вызов парсера из FastAPI

* Вызов парсера из FastAPI через очередь


## Реализация

### `main.py` Parser
```python
from typing import List

from fastapi import FastAPI, HTTPException
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, urlunparse

headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36'}


app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/parse")
def parse(url: str):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup.find('h1').string.strip('"')
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))


# urls = ['https://opticdevices.ru/category_27.html',
#         'https://opticdevices.ru/category_27_offset_12.html',
#         'https://opticdevices.ru/category_27_offset_24.html']


@app.get("/catalog")
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

### `main.py` Store
```python
class ParsedData(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str


DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://pguser:pgpwd123@db:5432/pgparser")
engine = create_engine(DATABASE_URL, echo=True)


SQLModel.metadata.create_all(engine)


app = FastAPI()


def get_session():
    with Session(engine) as session:
        yield session


@app.get("/parse")
def parse(url: str, session: Session = Depends(get_session)):
    try:
        params = {"url": url}
        parser = "http://parser:8001/catalog"
        response = requests.get(parser, params=params)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list):
            string_list = [str(item) for item in data]
        else:
            raise HTTPException(status_code=400, detail="unexpected response format (must be list)")

        parsed = []
        for item in string_list:
            params = {"url": item}
            parser = "http://parser:8001/parse"
            response = requests.get(parser, params=params)
            response.raise_for_status()
            title = response.content.decode("utf-8")

            with session:
                parsed_data = ParsedData(title=title)
                session.add(parsed_data)
                session.commit()
                parsed.append(title)

        return parsed

    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))
```


### `Dockerfile`
```
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
```

## Вывод
В этой части лабораторной работы были получены навыки по упаковке Fastapi приложения в Docker. Работа с образами и контейнерами.
