import asyncio
from datetime import datetime

import aiosqlite
from parse_and_save import parse_and_save_async
from parse_site import get_sources


db_path = "async_database.db"


async def create_db():
    async with aiosqlite.connect(db_path) as db:
        await db.execute("CREATE TABLE IF NOT EXISTS site_data (title TEXT)")
        await db.execute("DELETE FROM site_data")
        await db.commit()


async def store_string(string_to_store):
    async with aiosqlite.connect(db_path) as db:
        await db.execute("INSERT INTO site_data VALUES (?)", (string_to_store,))
        await db.commit()


async def async_worker():
    sources = ['https://opticdevices.ru' + i for i in get_sources()]

    start_time = datetime.now()
    await create_db()
    for url in sources:
        data = await parse_and_save_async(url)
        await store_string(data)
    end_time = datetime.now()
    print(f"time {end_time - start_time}")


asyncio.run(async_worker())
