import asyncio
import logging

from fastapi import FastAPI
from fastapi import Header
from fastapi import HTTPException
from fastapi import Request
from fastapi import Response
from fastapi.middleware.cors import CORSMiddleware

from .action import SummaryAction
from .content import standardize_content
from .queue_store import dequeue
from .queue_store import enqueue
from .settings_store import get_setting

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aggregator")

app = FastAPI()

API_KEY = get_setting("API_KEY")
ALLOWED_ORIGINS = get_setting("ALLOWED_ORIGINS")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

@app.post("/process_action/")
async def process_action(request: Request, authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    if not authorization.startswith("Api-Key "):
        raise HTTPException(status_code=403, detail="Invalid auth scheme")

    api_key = authorization.removeprefix("Api-Key ").strip()
    if api_key != API_KEY:
        return Response(status_code=401, content="Invalid or incorrect API key provided for authorization.")

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
