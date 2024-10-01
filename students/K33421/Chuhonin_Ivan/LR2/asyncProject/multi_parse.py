import multiprocessing
import time

from parse_and_save import parse_and_save
from parse_site import get_sources

if __name__ == '__main__':
    sources = ['https://opticdevices.ru' + i for i in get_sources()]

    start_time = time.time()
    num_processes = multiprocessing.cpu_count()

    with multiprocessing.Pool(processes=num_processes) as pool:
        pool.map(parse_and_save, sources)

    end_time = time.time()
    print(f"time {end_time-start_time} for {num_processes} cpu")
