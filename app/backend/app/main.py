from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api import ai

from app.core.config import settings
from app.core.database import engine, Base, get_db
from app.api import auth, products, sales, analytics, users, audit, forecast, predictions, models


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        Base.metadata.create_all(bind=engine)
        print("Database tables initialized successfully.")
    except Exception as e:
        print(f"Warning: could not auto-create tables on startup: {e}")
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for Product & Analytics Management System with MySQL and Streamlit integration.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(products.router)
app.include_router(sales.router)
app.include_router(analytics.router)
app.include_router(users.router)
app.include_router(audit.router)
app.include_router(ai.router)
app.include_router(forecast.router)
app.include_router(predictions.router)
app.include_router(models.router)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "project": settings.PROJECT_NAME}


@app.get("/health/ready", tags=["Health"])
def readiness_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as error:
        raise HTTPException(status_code=503, detail="Database is unavailable") from error
    return {"status": "ready", "database": "connected"}


@app.get("/", tags=["Root"])
def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "docs_url": "/docs",
        "health_url": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)