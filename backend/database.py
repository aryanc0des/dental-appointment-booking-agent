from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from config import settings

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def connect_db() -> None:
    global _client, _db
    _client = AsyncIOMotorClient(settings.MONGODB_URL)
    _db = _client[settings.MONGODB_DB]

    # Ensure indexes
    await _db.conversations.create_index("created_at")
    await _db.conversations.create_index("caller_id")
    await _db.appointments.create_index("appointment_time")
    await _db.appointments.create_index("created_at")

    print(f"✅ Connected to MongoDB: {settings.MONGODB_DB}")


async def close_db() -> None:
    global _client
    if _client:
        _client.close()
        print("MongoDB connection closed.")


def get_db() -> AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError("Database not initialized. Call connect_db() first.")
    return _db
