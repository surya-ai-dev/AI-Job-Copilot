# scripts/init_db.py
# Helper script to initialize database tables locally

import asyncio
from backend.app.database.session import engine, Base
from backend.app.auth.models.user_model import UserModel, RefreshTokenModel

async def init_models():
    async with engine.begin() as conn:
        print("Initializing database tables...")
        # Create all tables registered with Base metadata
        await conn.run_sync(Base.metadata.create_all)
        print("Database tables initialized successfully.")

if __name__ == "__main__":
    asyncio.run(init_models())
