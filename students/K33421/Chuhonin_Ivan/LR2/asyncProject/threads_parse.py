from threading import Thread
import time

from chunk import chunk_list
from parse_and_save import parse_and_save
from parse_site import get_sources


if __name__ == "__main__":
    num_threads = 6
    sources = ['https://opticdevices.ru' + i for i in get_sources()]

    start_time = time.time()
    chunks = list(chunk_list(sources, num_threads))
    for block in chunks:
        threads = []
        for i in range(num_threads):
            threads.append(Thread(target=parse_and_save, args=(block[i], )))

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

    end_time = time.time()
    print(f"Time taken: {end_time - start_time} seconds for {num_threads} threads")