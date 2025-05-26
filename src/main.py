from fastapi import FastAPI, Response, Request, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import logging

from .action import SummaryAction
from .queue import enqueue, dequeue
from .content import standardize_content

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


@app.on_event("startup")
async def startup():
    asyncio.create_task(process_queue())


async def process_queue():
    while True:
        action = await dequeue()
        logger.info(f"Processing: {action}")
        summaries = await standardize_content(action)
        logger.info(f"Standardized content: {summaries}")
