import asyncio
import logging
from config import bot, dp
from handlers import start, lessons

async def main():
    logging.basicConfig(level=logging.INFO)
    # Регистрируем роутеры
    dp.include_router(start.router)
    dp.include_router(lessons.router)
    # Запуск поллинга
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())