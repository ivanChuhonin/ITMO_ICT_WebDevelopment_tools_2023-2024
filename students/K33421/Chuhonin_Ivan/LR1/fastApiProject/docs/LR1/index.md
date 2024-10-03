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

В этом блоке мы описываем модель для дальнейшей программы. Указываются сущности, ключи и атрибуты.


### `main.py`
```python
from sqlmodel import SQLModel, create_engine, Session, select, col, alias

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
```


### `alembic`
```python
import sqlmodel
import sqlalchemy as sa

def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('book',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('book_name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('author', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('short_description', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('publishing_house', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('reader',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('full_name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('phone', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('bio', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('skills', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('hashed_password', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('phone')
    )
    op.create_table('bookinstance',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('id_book', sa.Integer(), nullable=False),
    sa.Column('id_reader', sa.Integer(), nullable=False),
    sa.Column('status_book', sa.Enum('New', 'Old', 'Lost', name='choicesbook'), nullable=False),
    sa.ForeignKeyConstraint(['id_book'], ['book.id'], ),
    sa.ForeignKeyConstraint(['id_reader'], ['reader.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('exchange',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('request_book', sa.Integer(), nullable=False),
    sa.Column('offer_book', sa.Integer(), nullable=False),
    sa.Column('exchange_start', sa.DateTime(), nullable=False),
    sa.Column('exchange_end', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['offer_book'], ['bookinstance.id'], ),
    sa.ForeignKeyConstraint(['request_book'], ['bookinstance.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('exchangehistory',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('request_book', sa.Integer(), nullable=False),
    sa.Column('offer_book', sa.Integer(), nullable=False),
    sa.Column('exchange_start', sa.DateTime(), nullable=False),
    sa.Column('exchange_end', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['offer_book'], ['bookinstance.id'], ),
    sa.ForeignKeyConstraint(['request_book'], ['bookinstance.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('exchangerequest',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('request_book', sa.Integer(), nullable=False),
    sa.Column('offer_book', sa.Integer(), nullable=False),
    sa.Column('request_date', sa.DateTime(), nullable=False),
    sa.Column('exchange_start', sa.DateTime(), nullable=False),
    sa.Column('exchange_end', sa.DateTime(), nullable=False),
    sa.Column('status', sa.Enum('Awaiting', 'Accepted', 'Denied', name='choices'), nullable=False),
    sa.ForeignKeyConstraint(['offer_book'], ['bookinstance.id'], ),
    sa.ForeignKeyConstraint(['request_book'], ['bookinstance.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('exchangerequest')
    op.drop_table('exchangehistory')
    op.drop_table('exchange')
    op.drop_table('bookinstance')
    op.drop_table('reader')
    op.drop_table('book')
    # ### end Alembic commands ###
```


## Ссылки на практические задания
1. https://github.com/ivanChuhonin/ITMO_ICT_WebDevelopment_tools_2023-2024/tree/main/students/K33421/Chuhonin_Ivan/LR1/fastApiProject/PR1/task1
2. https://github.com/ivanChuhonin/ITMO_ICT_WebDevelopment_tools_2023-2024/tree/main/students/K33421/Chuhonin_Ivan/LR1/fastApiProject/PR1/task2


## Вывод
В данной лабораторной работе были получены навыки по реализации полноценного серверного приложения с помощью фреймворка FastAPI. Также был получен опыт по реализации платформы для обмена книгами.