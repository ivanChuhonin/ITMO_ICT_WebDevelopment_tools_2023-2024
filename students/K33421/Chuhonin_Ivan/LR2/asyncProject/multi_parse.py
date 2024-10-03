import multiprocessing
from datetime import datetime

from db import create_db
from parse_and_save import parse_and_save
from parse_site import get_sources


dbname = 'multi_database.db'


if __name__ == '__main__':
    sources = [('https://opticdevices.ru' + i, dbname) for i in get_sources()]
    start_time = datetime.now()

    create_db(dbname)

    num_processes = multiprocessing.cpu_count()
    with multiprocessing.Pool(processes=num_processes) as pool:
        pool.map(parse_and_save, sources)

    end_time = datetime.now()
    print(f"Time taken: {end_time - start_time} seconds for {num_processes} threads")

