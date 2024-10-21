from fastapi import FastAPI
from app.api.v1.endpoints import camera, fish, llm, system

app = FastAPI()

app.include_router(camera.router, prefix="/api/v1/camera", tags=["camera"])
app.include_router(fish.router, prefix="/api/v1/fish", tags=["fish"])
app.include_router(llm.router, prefix="/api/v1/llm", tags=["llm"])
app.include_router(system.router, prefix="/api/v1/system", tags=["system"])
