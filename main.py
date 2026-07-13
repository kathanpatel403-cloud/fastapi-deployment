from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import Base, engine, get_db
from models import User
from schemas import UserCreate, UserOut, StandardResponse
from celery_app import send_email_task


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Asynchronously create tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="FastAPI deployment", version="1.0.0", lifespan=lifespan)


@app.get("/health", response_model=StandardResponse)
def health_check():
    """Health check endpoint"""
    return StandardResponse(data={}, status=1, message="Backend is healthy!")



@app.get("/", response_model=StandardResponse)
def root():
    return StandardResponse(data={}, status=1, message="Welcome to the FastAPI app")


@app.post("/users", response_model=StandardResponse[UserOut], status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.email == user_data.email))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")

    user = User(**user_data.model_dump())
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return StandardResponse(data=UserOut.model_validate(user), status=1, message="User created successfully")


@app.get("/users", response_model=StandardResponse[list[UserOut]])
async def list_users(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).offset(skip).limit(limit))
    users = result.scalars().all()
    return StandardResponse(data=[UserOut.model_validate(u) for u in users], status=1, message="Users retrieved successfully")


@app.get("/users/{user_id}", response_model=StandardResponse[UserOut])
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return StandardResponse(data=UserOut.model_validate(user), status=1, message="User retrieved successfully")


@app.post("/send-email", response_model=StandardResponse, status_code=status.HTTP_202_ACCEPTED)
def send_email(email: str, subject: str, message: str):
    """Triggers an asynchronous background task via Celery worker."""
    task = send_email_task.delay(email, subject, message)
    return StandardResponse(data={"task_id": task.id}, status=1, message="Task submitted to queue!")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
