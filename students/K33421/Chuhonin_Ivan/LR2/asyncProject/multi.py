import multiprocessing
import time


def sum_chunk(s, e):
    total = 0
    for j in range(s, e + 1):
        total += j
    return total


if __name__ == '__main__':
    start_time = time.time()
    num_processes = multiprocessing.cpu_count()
    chunk_size = 1000000 // num_processes
    pool = multiprocessing.Pool(processes=num_processes)
    results = []

    for i in range(num_processes):
        start = i * chunk_size + 1
        end = (i + 1) * chunk_size
        if i == num_processes - 1:
            end = 1000000
        results.append(pool.apply_async(sum_chunk, args=(start, end)))

    pool.close()
    pool.join()

    final_sum = sum([result.get() for result in results])
    end_time = time.time()
    print(f"Sum of numbers from 1 to 1000000: {final_sum}")
    print(f"time {end_time-start_time} for {num_processes} cpu")