import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.app.models.user import User
from src.app.core.security import get_password_hash

DATABASE_URL = "sqlite+aiosqlite:///./data/mes.db"
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

from src.app.db.base import Base
import src.app.models  # This registers all models with Base.metadata

async def insert_admin():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSessionLocal() as session:
        admin = User(
            username="admin",
            password_hash=get_password_hash("admin123"),
            role="ADMIN"
        )
        session.add(admin)
        await session.commit()
        print("Admin user inserted.")

asyncio.run(insert_admin())
