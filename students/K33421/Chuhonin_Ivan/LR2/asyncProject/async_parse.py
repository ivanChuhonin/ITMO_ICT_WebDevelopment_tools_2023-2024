import asyncio
import time

from parse_and_save import parse_and_save
from parse_site import get_sources


async def main():
    # tasks = [asyncio.create_task(await parse_and_save_async(url) for url in get_sources())]
    sources = ['https://opticdevices.ru' + i for i in get_sources()]
    tasks = [asyncio.create_task(parse_and_save(url) for url in sources)]
    await asyncio.gather(*tasks)

start_time = time.time()
asyncio.run(main())
end_time = time.time()
print(f"time {end_time - start_time}")
