import asyncio
import logging

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Request
from fastapi import Response
from fastapi import Security
from fastapi import status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader

from src.action import SummaryAction
from src.content import standardize_content
from src.queue_store import dequeue
from src.queue_store import enqueue
from src.settings_store import get_setting

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("aggregator")

app = FastAPI()


ALLOWED_API_KEY = get_setting("API_KEY")
api_key_header = APIKeyHeader(name="x-api-key")
# ALLOWED_ORIGINS = get_setting("ALLOWED_ORIGINS")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=ALLOWED_ORIGINS,
#     allow_methods=["*"],
#     allow_headers=["*"],
#     allow_credentials=True,
# )

@app.post("/process_action/")
async def process_action(request: Request, key: str = Security(api_key_header)):
    print("TEST", key, ALLOWED_API_KEY)
    if not key or key != ALLOWED_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid API key")
    data = await request.json()

    try:
        content = data["content"]
        source = data["source"]
    except KeyError as e:
        return Response(status_code=400, content=f"Missing key: {e}")

    await enqueue(SummaryAction(content, source))
    return Response(status_code=200, content="Action queued.")


background_tasks = set()

@app.on_event("startup")
async def startup():
    task = asyncio.create_task(process_queue())
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)


async def process_queue():
    while True:
        action = await dequeue()
        logger.info("Processing: %s", action)
        summaries = await standardize_content(action)
        logger.info("Standardized content: %s", summaries)
