import asyncio
import logging
from src.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Starting ETHUSDT own movement analyzer...")
    # Здесь будет инициализация и запуск всех компонентов
    await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())