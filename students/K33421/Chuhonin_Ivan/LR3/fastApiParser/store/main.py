import os
from sqlmodel import SQLModel, create_engine, Session, Field
from fastapi import FastAPI, HTTPException, Depends
import requests
from typing import Optional


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
