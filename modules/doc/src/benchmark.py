import asyncio
import time

from src.server import SSEManager

class MockQueue:
    def __init__(self, delay=0.01):
        self.delay = delay

    async def put(self, message):
        await asyncio.sleep(self.delay)

async def main():
    num_connections = 100
    delay = 0.01
    print(f"Measuring broadcast time with {num_connections} connections, {delay}s delay each...")

    manager = SSEManager()
    for _ in range(num_connections):
        manager.active_queues.append(MockQueue(delay))

    start_time = time.perf_counter()
    await manager.broadcast("test message")
    end_time = time.perf_counter()
    print(f"Time taken: {end_time - start_time:.4f} seconds")

if __name__ == "__main__":
    asyncio.run(main())
