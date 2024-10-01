from threading import Thread
import time


def calculate_sum(s, e, result, index):
    total = sum(range(s, e + 1))
    result[index] = total


if __name__ == "__main__":
    start_time = time.time()
    num_threads = 8
    range_per_thread = 125000
    threads = []
    results = [0] * num_threads

    for i in range(num_threads):
        start = i * range_per_thread + 1
        end = (i + 1) * range_per_thread
        thread = Thread(target=calculate_sum, args=(start, end, results, i))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    total_sum = sum(results)
    print(f"The sum from 1 to {num_threads * range_per_thread} is: {total_sum}")
    end_time = time.time()
    print(f"Time taken: {end_time - start_time} seconds for {num_threads} threads")