from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from routers import router
from database import database, engine
from models import Base


app = FastAPI(redirect_slashes=False)

def prepare_database() -> None:
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        result = conn.execute(
            text(
                """
                SELECT udt_name
                FROM information_schema.columns
                WHERE table_name = 'speakers' AND column_name = 'embedding'
                """
            )
        ).fetchone()
        if result and result[0] != "vector":
            conn.execute(
                text(
                    """
                    ALTER TABLE speakers
                    ALTER COLUMN embedding TYPE vector(256)
                    USING embedding::text::vector
                    """
                )
            )
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
    prepare_database()
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
