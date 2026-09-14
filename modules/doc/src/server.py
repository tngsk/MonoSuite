import json
import logging
import aiofiles
import tomllib
import asyncio
from typing import List
from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path
import os

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def get_security_config() -> dict:
    config = {
        "origins": ["http://localhost:8000", "http://127.0.0.1:8000"],
        "methods": ["*"],
        "headers": ["*"],
        "max_upload_size": 1024 * 1024  # Default 1MB
    }

    config_paths = [
        Path.cwd() / "config.toml",
        Path(__file__).resolve().parent.parent / "config.toml",
    ]
    config_path = next((p for p in config_paths if p.is_file()), None)
    if config_path:
        try:
            with open(config_path, "rb") as f:
                config_data = tomllib.load(f)
                if "security" in config_data:
                    sec = config_data["security"]
                    if "cors-allowed-origins" in sec:
                        config["origins"] = sec["cors-allowed-origins"]
                    if "max-upload-size" in sec:
                        config["max_upload_size"] = sec["max-upload-size"]
        except Exception as e:
            logger.warning(f"Could not load security config from config.toml: {e}")

    # Enforce production security rules
    is_production = os.environ.get("ENVIRONMENT", "").lower() == "production"
    if is_production:
        # Remove wildcard and null from origins
        config["origins"] = [
            origin for origin in config["origins"]
            if origin not in ("*", "null")
        ]
        # If no origins left, restrict completely
        if not config["origins"]:
            config["origins"] = ["http://localhost:8000"] # fallback to least privilege

        # Restrict methods and headers
        config["methods"] = ["GET", "POST", "OPTIONS"]
        config["headers"] = ["Content-Type", "Content-Length", "Accept"]

    return config

def get_allowed_origins() -> List[str]:
    # Keeping this for backward compatibility with tests
    return get_security_config()["origins"]


data_queue = None
worker_task = None

async def data_writer_worker():
    while True:
        data = None
        try:
            data = await data_queue.get()
            if data is None:
                data_queue.task_done()
                break
            async with aiofiles.open("data.jsonl", "a", encoding="utf-8") as f:
                await f.write(json.dumps(data) + "\n")
            data_queue.task_done()
        except Exception as e:
            logger.error(f"Error in data_writer_worker: {e}")
            if data is not None:
                data_queue.task_done()

@asynccontextmanager
async def lifespan(app: FastAPI):
    global worker_task, data_queue
    data_queue = asyncio.Queue()
    worker_task = asyncio.create_task(data_writer_worker())
    yield
    await data_queue.put(None)
    if worker_task:
        await worker_task

app = FastAPI(title="Mono Sync Server", lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_security_config()["origins"],
    allow_credentials=False,
    allow_methods=get_security_config()["methods"],
    allow_headers=get_security_config()["headers"],
)


class SSEManager:
    def __init__(self):
        self.active_queues: List[asyncio.Queue] = []

    def connect(self) -> asyncio.Queue:
        q = asyncio.Queue()
        self.active_queues.append(q)
        logger.info(f"SSE client connected. Active: {len(self.active_queues)}")
        return q

    def disconnect(self, q: asyncio.Queue):
        if q in self.active_queues:
            self.active_queues.remove(q)
            logger.info(f"SSE client disconnected. Active: {len(self.active_queues)}")

    async def broadcast(self, message: str):
        # ⚡ Bolt Optimization: Use asyncio.gather to concurrently broadcast to all active queues
        # instead of awaiting them sequentially in a loop. This reduces broadcast time
        # from O(N) to roughly O(1) for large numbers of connected clients.
        if self.active_queues:
            await asyncio.gather(*(q.put(message) for q in self.active_queues))


sse_manager = SSEManager()


@app.get("/api/sync/stream")
async def sync_stream(request: Request):
    async def event_generator():
        q = sse_manager.connect()
        try:
            while True:
                if await request.is_disconnected():
                    break
                # Wait for new message
                message = await q.get()
                yield f"data: {message}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            sse_manager.disconnect(q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )

@app.post("/api/sync")
async def sync_post(request: Request):
    try:
        body = await request.body()
        data = body.decode("utf-8")
        await sse_manager.broadcast(data)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error in sync post: {e}")
        return {"status": "error", "message": str(e)}


@app.post("/api/data")
async def receive_data(request: Request):
    try:
        config = get_security_config()
        max_size = config["max_upload_size"]

        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > max_size:
            return {"status": "error", "message": "Payload too large"}

        body = b""
        async for chunk in request.stream():
            body += chunk
            if len(body) > max_size:
                return {"status": "error", "message": "Payload too large"}

        data = json.loads(body)
        await data_queue.put(data)
        return {"status": "success"}
    except json.JSONDecodeError:
        return {"status": "error", "message": "Invalid JSON"}
    except Exception as e:
        logger.error(f"Error saving data: {e}")
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
