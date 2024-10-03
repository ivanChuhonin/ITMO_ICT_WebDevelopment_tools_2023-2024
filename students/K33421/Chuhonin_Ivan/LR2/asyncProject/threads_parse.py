from datetime import datetime
from threading import Thread
from typing import List

from db import create_db
from parse_and_save import parse_and_save
from parse_site import get_sources


dbname = 'threads_database.db'


def chunk_list(lst: List[str], n: int) -> List[str]:
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


if __name__ == '__main__':
    sources = ['https://opticdevices.ru' + i for i in get_sources()]

    start_time = datetime.now()
    num_threads = 6

    create_db(dbname)

    chunks = list(chunk_list(sources, num_threads))
    for block in chunks:
        threads = []
        for i in range(num_threads):
            threads.append(Thread(target=parse_and_save, args=((block[i], dbname, ), )))

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

    end_time = datetime.now()
    print(f"Time taken: {end_time - start_time} seconds for {num_threads} threads")