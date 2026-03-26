from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import router
from database import database, engine
from models import Base


app = FastAPI(redirect_slashes=False)

# автоматическое создание таблиц при запуске
Base.metadata.create_all(bind=engine)

#CORS поддержка
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
