from redis import Redis
from sqlalchemy import create_engine, text

from app.core.config import settings


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)


def test_postgresql():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        return result.scalar()


redis_client = Redis.from_url(
    settings.redis_url,
    decode_responses=True,
)


def test_redis():
    return redis_client.ping()