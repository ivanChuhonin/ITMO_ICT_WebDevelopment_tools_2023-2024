from datetime import timedelta, datetime
from typing import List, Annotated

from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import SQLModel, create_engine, Session, select, col, alias
from fastapi import FastAPI, HTTPException, Depends

from auth import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, get_password_hash, verify_password, \
    get_current_user_phone
from models import Reader, Book, BookInstance, Exchange, ExchangeHistory, ExchangeRequest, Token, User, ChoicesBook, \
    BookInfoInstance, ExchangeRequestInfo, CHOICES
from contextlib import asynccontextmanager


sqlite_url = f"sqlite:///./database.db"
connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=True, connect_args=connect_args)


@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield


app = FastAPI(lifespan=lifespan)


def get_reader(current_user_phone: str, session: Session):
    statement = select(Reader).where(Reader.phone == current_user_phone)
    result = session.exec(statement)
    db_reader = result.first()
    if db_reader is None:
        raise HTTPException(status_code=404, detail="Reader not found")
    return db_reader


def get_user(phone: str):
    with Session(engine) as session:
        statement = select(Reader).where(Reader.phone == phone)
        result = session.exec(statement)
        reader = result.first()
        if reader is None:
            raise HTTPException(status_code=404, detail="Reader not found")
        return reader


def authenticate_user(phone: str, password: str):
    user = get_user(phone)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


@app.post("/readers/", response_model=Reader)
def create_reader(user: User):
    with Session(engine) as session:
        statement = select(Reader).where(Reader.phone == user.phone)
        existed_users = session.exec(statement)
        reader = existed_users.first()
        if reader:
            raise HTTPException(status_code=404, detail="Reader existed")

        reader = Reader(phone=user.phone, full_name=user.full_name, bio=user.bio, skills=user.skills,
                        hashed_password=get_password_hash(user.password))
        session.add(reader)
        session.commit()
        session.refresh(reader)
        reader.hashed_password = ''
        return reader


@app.post("/token")
def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect phone or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.phone}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@app.put("/readers/", response_model=Reader)
def update_reader(current_user_phone: Annotated[str, Depends(get_current_user_phone)], reader: Reader):
    with Session(engine) as session:
        db_reader = get_reader(current_user_phone, session)

        if reader.full_name is not None:
            db_reader.full_name = reader.full_name
        if reader.bio is not None:
            db_reader.bio = reader.bio
        if reader.skills is not None:
            db_reader.skills = reader.skills
        session.commit()
        session.refresh(db_reader)
        db_reader.hashed_password = None
        return db_reader


@app.get("/me", response_model=Reader)
def update_reader(current_user_phone: Annotated[str, Depends(get_current_user_phone)]):
    with Session(engine) as session:
        db_reader = get_reader(current_user_phone, session)
        db_reader.hashed_password = None
        return db_reader


@app.get("/readers/", response_model=List[Reader])
def update_reader(current_user_phone: Annotated[str, Depends(get_current_user_phone)],
               skip: int = 0, limit: int = 10):
    with Session(engine) as session:
        statement = select(Reader).offset(skip).limit(limit)
        readers = session.exec(statement).all()
        for reader in readers:
            reader.hashed_password = None
        return readers


@app.get("/books/", response_model=List[Book])
def read_books(current_user_phone: Annotated[str, Depends(get_current_user_phone)],
               skip: int = 0, limit: int = 10, q: str = None):
    with Session(engine) as session:
        if q is None:
            statement = select(Book).offset(skip).limit(limit)
        else:
            statement = select(Book).where(col(Book.short_description).contains(f"{q}")).offset(skip).limit(limit)
        books = session.exec(statement).all()
        return books


@app.post("/books/", response_model=Book)
def create_book(current_user_phone: Annotated[str, Depends(get_current_user_phone)],
                book: Book):
    with Session(engine) as session:
        session.add(book)
        session.commit()
        session.refresh(book)
        return book


@app.get("/books/{book_id}", response_model=Book)
def read_book(current_user_phone: Annotated[str, Depends(get_current_user_phone)],
              book_id: int):
    with Session(engine) as session:
        book = session.get(Book, book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        return book


@app.put("/books/{book_id}", response_model=Book)
def update_book(current_user_phone: Annotated[str, Depends(get_current_user_phone)],
                book_id: int, book: Book):
    with Session(engine) as session:
        db_book = session.get(Book, book_id)
        if not db_book:
            raise HTTPException(status_code=404, detail="Book not found")
        book.id = db_book.id  # Сохраняем id для обновления
        session.merge(book)
        session.commit()
        session.refresh(db_book)
        return db_book


@app.post("/book-instances/", response_model=BookInfoInstance)
def create_book_instance(current_user_phone: Annotated[str, Depends(get_current_user_phone)],
                         book_instance: BookInstance):
    with Session(engine) as session:
        db_reader = get_reader(current_user_phone, session)

        book = session.get(Book, book_instance.id_book)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        book_instance.id_reader = db_reader.id
        session.add(book_instance)
        session.commit()
        session.refresh(book_instance)

        return get_book_info_instance(book_instance, session)


@app.get("/book-my-instances/", response_model=List[BookInfoInstance])
def read_book_my_instances(current_user_phone: Annotated[str, Depends(get_current_user_phone)],
                        skip: int = 0, limit: int = 10):
    with Session(engine) as session:
        db_reader = get_reader(current_user_phone, session)

        statement = select(BookInstance).where(BookInstance.id_reader == db_reader.id and
                                               BookInstance.status_book != ChoicesBook.Lost).offset(skip).limit(limit)
        book_instances = session.exec(statement).all()
        book_info_instances: List[BookInfoInstance] = []
        for book_instance in book_instances:
            book_info_instances.append(get_book_info_instance(book_instance, session))
        return book_info_instances


@app.get("/book-instances/", response_model=List[BookInfoInstance])
def read_book_instances(current_user_phone: Annotated[str, Depends(get_current_user_phone)],
                        id_book: int,
                        skip: int = 0, limit: int = 10):
    with Session(engine) as session:
        statement = select(BookInstance).where(BookInstance.id_book == id_book and
                                               BookInstance.status_book != ChoicesBook.Lost).offset(skip).limit(limit)
        book_instances = session.exec(statement).all()
        book_info_instances: List[BookInfoInstance] = []
        for book_instance in book_instances:
            book_info_instances.append(get_book_info_instance(book_instance, session))
        return book_info_instances


def get_book_info_instance(book_instance: BookInstance, session: Session):
    book = session.get(Book, book_instance.id_book)
    return BookInfoInstance(id=book_instance.id,
                            id_book=book_instance.id_book,
                            id_reader=book_instance.id_reader,
                            book_name=book.book_name,
                            author=book.author,
                            short_description=book.short_description,
                            publishing_house=book.publishing_house,
                            status_book=book_instance.status_book)


@app.put("/book-instances/{book_instance_id}", response_model=BookInfoInstance)
def update_book_instance(current_user_phone: Annotated[str, Depends(get_current_user_phone)],
                         book_instance_id: int, book_instance: BookInstance):
    with Session(engine) as session:
        db_reader = get_reader(current_user_phone, session)

        db_book_instance = session.get(BookInstance, book_instance_id)
        if db_book_instance is None:
            raise HTTPException(status_code=404, detail="BookInstance not found")
        if db_book_instance.id_reader != db_reader.id:
            raise HTTPException(status_code=401, detail="Not Authorized edit BookInstance")

        if book_instance.id_book is not None:
            db_book_instance.id_book = book_instance.id_book
        if book_instance.status_book is not None:
            db_book_instance.status_book = book_instance.status_book
        session.add(db_book_instance)
        session.commit()
        session.refresh(db_book_instance)

        return get_book_info_instance(db_book_instance, session)


# CRUD операции для ExchangeRequest
@app.post("/exchange-requests/", response_model=ExchangeRequestInfo)
def create_exchange_request(current_user_phone: Annotated[str, Depends(get_current_user_phone)],
                            exchange_request: ExchangeRequest):

    with Session(engine) as session:
        db_reader = get_reader(current_user_phone, session)
        book_instance_request = session.get(BookInstance, exchange_request.request_book)
        book_instance_offer = session.get(BookInstance, exchange_request.offer_book)
        is_authorized = book_instance_request.id_reader == db_reader.id or book_instance_offer.id_reader == db_reader.id
        if not is_authorized:
            raise HTTPException(status_code=401, detail="You cannot create this exchange request")

        session.add(exchange_request)
        exchange_request.request_date = None
        exchange_request.status = None
        exchange_request.exchange_start = datetime.fromisoformat(exchange_request.exchange_start)
        exchange_request.exchange_end = datetime.fromisoformat(exchange_request.exchange_end)
        session.commit()
        session.refresh(exchange_request)

        book_instance_request_info = get_book_info_instance(book_instance_request, session)
        book_instance_offer_info = get_book_info_instance(book_instance_offer, session)

        return ExchangeRequestInfo(id=exchange_request.id,
                                   request_book=exchange_request.request_book,
                                   request_book_name=book_instance_request_info.book_name,
                                   offer_book=exchange_request.offer_book,
                                   offer_book_name=book_instance_offer_info.book_name,
                                   request_date=exchange_request.request_book,
                                   exchange_start=exchange_request.exchange_start,
                                   exchange_end=exchange_request.exchange_end,
                                   status=exchange_request.status)


@app.get("/exchange-requests/", response_model=List[ExchangeRequestInfo])
def read_exchange_requests(current_user_phone: Annotated[str, Depends(get_current_user_phone)],
                           skip: int = 0, limit: int = 10):
    with Session(engine) as session:
        db_reader = get_reader(current_user_phone, session)

        request = alias(BookInstance)
        offer = alias(BookInstance)

        statement = select(ExchangeRequest
            ).join(request, ExchangeRequest.request_book == request.c.id
            ).join(offer, ExchangeRequest.offer_book == offer.c.id
            ).where(request.c.id_reader == db_reader.id or offer.c.id_reader == db_reader.id
            ).offset(skip).limit(limit)

        exchange_requests = session.exec(statement).all()

        exchange_request_info_list: List[ExchangeRequestInfo] = []
        for exchange_request, book_instance_request, book_instance_offer in exchange_requests:
            book_instance_request_info = get_book_info_instance(book_instance_request, session)
            book_instance_offer_info = get_book_info_instance(book_instance_offer, session)
            exchange_request_info_list.append(ExchangeRequestInfo(id=exchange_request.id,
                                                                  request_book=exchange_request.request_book,
                                                                  request_book_name=book_instance_request_info.book_name,
                                                                  offer_book=exchange_request.offer_book,
                                                                  offer_book_name=book_instance_offer_info.book_name,
                                                                  request_date=exchange_request.request_book,
                                                                  exchange_start=exchange_request.exchange_start,
                                                                  exchange_end=exchange_request.exchange_end,
                                                                  status=exchange_request.status))
        return exchange_requests


@app.put("/exchange-requests/{exchange_request_id}", response_model=Exchange)
def update_exchange_request(current_user_phone: Annotated[str, Depends(get_current_user_phone)],
                            exchange_request_id: int, status: CHOICES):
    with (Session(engine) as session):
        db_reader = get_reader(current_user_phone, session)
        db_exchange_request = session.get(ExchangeRequest, exchange_request_id)
        if db_exchange_request is None:
            raise HTTPException(status_code=404, detail="ExchangeRequest not found")
        if db_exchange_request.status == CHOICES.Accepted:
            raise HTTPException(status_code=403, detail="ExchangeRequest cannot be changed")

        db_book_instance_request = session.get(BookInstance, db_exchange_request.request_book)
        db_book_instance_offer = session.get(BookInstance, db_exchange_request.offer_book)
        is_authorized = db_book_instance_request.id_reader == db_reader.id or db_book_instance_offer.id_reader == db_reader.id
        if not is_authorized:
            raise HTTPException(status_code=401, detail="You cannot modify this exchange request")

        db_exchange_request.status = status
        session.add(db_exchange_request)
        session.commit()
        session.refresh(db_exchange_request)

        exchange = Exchange(request_book=db_exchange_request.request_book,
                            offer_book=db_exchange_request.offer_book,
                            exchange_start=db_exchange_request.exchange_start,
                            exchange_end=db_exchange_request.exchange_end)
        session.add(exchange)
        session.commit()
        session.refresh(exchange)
        return exchange


# CRUD операции для Exchange
@app.get("/exchanges/", response_model=List[Exchange])
def read_exchanges(current_user_phone: Annotated[str, Depends(get_current_user_phone)],
                   skip: int = 0, limit: int = 10):
    with (Session(engine) as session):
        db_reader = get_reader(current_user_phone, session)

        request = alias(BookInstance)
        offer = alias(BookInstance)
        statement = select(Exchange
            ).join(request, Exchange.request_book == request.c.id
            ).join(offer, Exchange.offer_book == offer.c.id
            ).where(request.c.id_reader == db_reader.id or offer.c.id_reader == db_reader.id
            ).offset(skip).limit(limit)
        exchanges = session.exec(statement).all()

        return exchanges


@app.put("/exchanges/{exchange_id}", response_model=ExchangeHistory)
def update_exchange(current_user_phone: Annotated[str, Depends(get_current_user_phone)],
                    exchange_id: int, exchange: Exchange):
    with Session(engine) as session:
        db_reader = get_reader(current_user_phone, session)
        db_exchange = session.get(Exchange, exchange_id)
        if db_exchange is None or exchange.exchange_end is None:
            raise HTTPException(status_code=404, detail="Exchange not found")

        book_instance_request = session.get(BookInstance, db_exchange.request_book)
        book_instance_offer = session.get(BookInstance, db_exchange.offer_book)
        if not (book_instance_request.id_reader == db_reader.id or book_instance_offer.id_reader==db_reader.id):
            raise HTTPException(status_code=401, detail="You cannot edit this exchange record")

        exchange_history = ExchangeHistory(request_book=db_exchange.request_book,
                                           offer_book=db_exchange.offer_book,
                                           exchange_start=db_exchange.exchange_start,
                                           exchange_end=exchange.exchange_end)

        session.add(exchange_history)
        session.delete(db_exchange)
        session.commit()
        return exchange_history


@app.get("/exchange-history/", response_model=List[ExchangeHistory])
def exchange_histories(current_user_phone: Annotated[str, Depends(get_current_user_phone)],
                   skip: int = 0, limit: int = 10):
    with Session(engine) as session:
        db_reader = get_reader(current_user_phone, session)

        request = alias(BookInstance)
        offer = alias(BookInstance)

        statement = select(ExchangeHistory
            ).join(request, ExchangeHistory.request_book == request.c.id
            ).join(offer, ExchangeHistory.offer_book == offer.c.id
            ).where(request.c.id_reader == db_reader.id or offer.c.id_reader == db_reader.id
            ).offset(skip).limit(limit)

        exchanges_histories = session.exec(statement).all()
        return exchanges_histories