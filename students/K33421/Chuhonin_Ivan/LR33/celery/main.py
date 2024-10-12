from fastapi import FastAPI
from tasks import parser, catalog
from celery.result import AsyncResult


app = FastAPI()


@app.post("/parser/")
async def create_task(url: str):
    task = parser.delay(url)
    return {"task_id": task.id}


@app.post("/catalog/")
async def create_task(url: str):
    task = catalog.delay(url)
    return {"task_id": task.id}


@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    task_result = AsyncResult(task_id)
    result = {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result
    }
    return result
