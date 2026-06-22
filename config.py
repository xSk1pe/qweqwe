import os
from aiogram import Bot, Dispatcher

TOKEN = ""

# Переменные окружения HTTP_PROXY уже заданы в bat-файле,
# и aiohtt p автоматически их подхватит при создании стандартной сессии.
bot = Bot(token=TOKEN)
dp = Dispatcher()