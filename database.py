import asyncpg
import logging
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        """Создание пула подключений"""
        if self.pool is None:
            try:
                self.pool = await asyncpg.create_pool(
                    host=DB_HOST,
                    port=DB_PORT,
                    database=DB_NAME,
                    user=DB_USER,
                    password=DB_PASSWORD,
                    min_size=5,
                    max_size=20,
                )
                logger.info("✅ Успешное подключение к PostgreSQL")
            except Exception as e:
                logger.error(f"❌ Ошибка подключения к БД: {e}")
                raise

    async def close(self):
        """Закрытие пула"""
        if self.pool:
            await self.pool.close()
            logger.info("🔌 Подключение к БД закрыто")

    async def execute(self, query: str, *args):
        """Выполнение запроса без возврата данных (INSERT, UPDATE, DELETE)"""
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args):
        """Получение всех строк"""
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        """Получение одной строки"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)


# Создаём глобальный экземпляр
db = Database()