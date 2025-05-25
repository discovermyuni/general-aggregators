from fastapi import FastAPI, Response, Request
import asyncio

from .action import SummaryAction
from .queue import enqueue, dequeue
from .content import standardize_content

app = FastAPI()

# example target url
TARGET_URL = "http://localhost:8000/api/recieve_summary"

# TODO: change the API url i dont like how it looks
@app.post("/action/")
async def process_action(request: Request):
    # TODO: add authentication
    
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
        print(f"Processing: {action}")
        summaries = await standardize_content(action)
        print(f"Standardized content: {summaries}")

