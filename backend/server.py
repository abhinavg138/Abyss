from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.api import router

app = FastAPI(title="Abyss")

app.include_router(router)

# Serve everything in frontend/ as /static/...
app.mount("/static", StaticFiles(directory="frontend"), name="static")
app.mount("/data/uploads", StaticFiles(directory="data/uploads"), name="data_uploads")


@app.get("/")
async def home():
    return FileResponse("frontend/index.html")
