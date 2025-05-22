from fastapi import FastAPI, Response

from .action import SummaryAction
from .queue import enqueue, dequeue
from .content import standardize_content, send_content

app = FastAPI()

TARGET_URL = "http://localhost:8000/api/recieve_summary"

@app.post("/action/")
async def process_action(content_type: int, content: str, source: str):
    await enqueue(SummaryAction(content_type, content, source))
    return Response(status_code=200, content="Action queued.")


@app.on_event("startup")
async def startup():
    import asyncio
    asyncio.create_task(process_queue())


async def process_queue():
    while True:
        action = await dequeue()
        print(f"Processing: {action}")
        summary = await standardize_content(action)
        await send_content(summary, TARGET_URL)
        