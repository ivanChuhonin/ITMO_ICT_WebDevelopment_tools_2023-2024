from enum import Enum
from typing import Optional, List

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


temp_bd = [{  "id": 1,
              "title": "Как работают над сценарием в Южной Калифорнии",
              "author": "Д. Говард, Э. Мабли",
              "genre": "сценарное мастерство",
              "publisher": "Альпина",
              "year_of_publication": 2021,
              "description": "Как создать сценарий фильма",
              "owner_id": {
                  "id": 1,
                  "username": "ivan12345",
                  "hashed_password": "ivan12345",
                  "name": "Ivan",
                  "surname": "Sergeev",
                  "email": "ivaCh@mail.ru"
              }},
           {"id": 2,
            "title": "Воспитание чувств",
            "author": "Г. Флобер",
            "genre": "зарубежная классика",
            "publisher": "Азбука",
            "year_of_publication": 2022,
            "description": "Роман отражающий 2 взгляда на жизнь",
            "owner_id": {
                "id": 2,
                "username": "anna12345",
                "hashed_password": "anna12345",
                "name": "Anna",
                "surname": "Matveeva",
                "email": "Mata@mail.ru"
            }},
            { "id": 3,
              "title": "Когда плакал Ницше",
              "author": "И. Ялом",
              "genre": "психология",
              "publisher": "Бомбора",
              "year_of_publication": 2019,
              "description": "Два лечебных сеанса венского терапевта и великого философа",
              "owner_id": {
                  "id": 1,
                  "username": "ivan12345",
                  "hashed_password": "ivan12345",
                  "name": "Ivan",
                  "surname": "Sergeev",
                  "email": "ivaCh@mail.ru"
              }}
           ]


class Genres(Enum):
    fantasy = "фантастика"
    detectives = "зарубежная классика"
    romance = "психология"
    thrillers = "драма"
    horrors = "сценарное мастерство"


class Books(BaseModel):
    title: str
    author: str
    genre: Genres
    publisher: str
    year_of_publication: int
    description: str


class Users(BaseModel):
    name: str
    surname: str
    email: str
    books: List[Books] = []


@app.get("/")
def hello():
    return "Hello, Ivan!"


@app.get("/books_list")
def books_list() -> List[Books]:
    return temp_bd


@app.get("/books/{books_id}")
def books_get(books_id: int) -> List[Books]:
    return [books for books in temp_bd if books.get("id") == books_id]


@app.post("/books")
def books_create(books: Books):
    books_to_append = books.model_dump()
    temp_bd.append(books_to_append)
    return {"status": 200, "data": books}


@app.delete("/books/delete{books_id}")
def books_delete(books_id: int):
    for i, books in enumerate(temp_bd):
        if books.get("id") == books_id:
            temp_bd.pop(i)
            break
    return {"status": 201, "message": "deleted"}


@app.put("/books{books_id}")
def books_update(books_id: int, books: Books) -> List[Books]:
    for bok in temp_bd:
        if bok.get("id") == books_id:
            books_to_append = books.model_dump()
            temp_bd.remove(bok)
            temp_bd.append(books_to_append)
    return temp_bd