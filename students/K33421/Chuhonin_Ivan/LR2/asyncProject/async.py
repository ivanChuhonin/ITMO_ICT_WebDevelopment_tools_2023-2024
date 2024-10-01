import asyncio
import time


async def sum_range(s, e):
    total = 0
    for j in range(s, e + 1):
        total += j
    return total


async def main():
    tasks = [
        asyncio.create_task(sum_range(1, 125000)),
        asyncio.create_task(sum_range(125001, 250000)),
        asyncio.create_task(sum_range(250001, 500000)),
        asyncio.create_task(sum_range(500001, 750000)),
        asyncio.create_task(sum_range(750001, 1000001)),
    ]
    results = await asyncio.gather(*tasks)
    print(f"Sum: {sum(results)}")


start_time = time.time()
asyncio.run(main())
end_time = time.time()
print(f"time {end_time - start_time}")
