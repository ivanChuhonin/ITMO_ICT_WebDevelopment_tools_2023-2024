# Лабораторная работа №1

## Цель лабораторной работы

Научиться реализовывать полноценное серверное приложение с помощью фреймворка FastAPI с применением дополнительных средств и библиотек.

## Описание работы

Задача - Разработка веб-приложения для буккроссинга. Создать веб-приложение, которое позволит пользователям обмениваться книгами между собой. Это приложение должно облегчать процесс обмена книгами, позволяя пользователям находить книги, которые им интересны, и находить новых пользователей для обмена книгами. Функционал веб-приложения должен включать следующее:

* Создание профилей: Возможность пользователям создавать профили, указывать информацию о себе, своих навыках, опыте работы и предпочтениях по проектам.

* Добавление книг в библиотеку: Пользователи могут добавлять книги, которыми они готовы поделиться, в свою виртуальную библиотеку на платформе.

* Поиск и запросы на обмен: Функционал поиска книг в библиотеке других пользователей. Возможность отправлять запросы на обмен книгами другим пользователям.

* Управление запросами и обменами: Возможность просмотра и управления запросами на обмен. Возможность подтверждения или отклонения запросов на обмен.


Критерии. Функционал включает в себя:
* Авторизацию и регистрацию
* Генерацию JWT-токенов
* Аутентификацию по JWT-токену
* Хэширование паролей
* Дополнительные АПИ-методы для получения информации о пользователе, списка пользователей и смене пароля


## Реализация

### `models.py`
```python
from sqlmodel import Field, SQLModel

class Token(SQLModel):
    access_token: str
    token_type: str


class Reader(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("phone"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    full_name: str
    phone: str
    bio: str
    skills: str
    hashed_password: str

    def __str__(self):
        return self.full_name


class User(SQLModel):
    full_name: str
    phone: str
    bio: str
    skills: str
    password: str = None


class Book(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    book_name: str
    author: str
    short_description: str
    publishing_house: str


class ChoicesBook(Enum):
    New = 'New'
    Old = 'Old'
    Lost = 'Lost'


class BookInstance(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    id_book: int = Field(foreign_key="book.id")
    id_reader: int = Field(foreign_key="reader.id")
    status_book: ChoicesBook


class CHOICES(Enum):
    Awaiting = 'Awaiting'
    Accepted = 'Accepted'
    Denied = 'Denied'


class BookInfoInstance(SQLModel):
    id: int
    id_book: int
    id_reader: int
    book_name: str
    author: str
    short_description: str
    publishing_house: str
    status_book: ChoicesBook


class ExchangeRequest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    request_book: int = Field(foreign_key="bookinstance.id")
    offer_book: int = Field(foreign_key="bookinstance.id")
    request_date: datetime = Field(default_factory=datetime.utcnow)
    exchange_start: datetime = Field(default=None)
    exchange_end: datetime = Field(default=None)
    status: CHOICES = Field(default=CHOICES.Awaiting)


class ExchangeRequestInfo(SQLModel):
    id: int
    request_book: int
    request_book_name: str
    offer_book: int
    offer_book_name: str
    request_date: datetime
    exchange_start: datetime
    exchange_end: datetime
    status: CHOICES


class Exchange(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    request_book: int = Field(foreign_key="bookinstance.id")
    offer_book: int = Field(foreign_key="bookinstance.id")
    exchange_start: datetime = Field(default=None)
    exchange_end: datetime = Field(default=None)


class ExchangeHistory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    request_book: int = Field(foreign_key="bookinstance.id")
    offer_book: int = Field(foreign_key="bookinstance.id")
    exchange_start: datetime
    exchange_end: datetime
```


### `main.py`
```python

```
