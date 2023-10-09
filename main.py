import asyncio
import logging
import sys
from os import getenv

from aiogram import Bot, Dispatcher, Router, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram import types
from aiogram.utils.markdown import hbold

from support import support_router
from lms import lms_router

# PROD
# TELEGRAM_TOKEN = '6302082234:AAF_5Mi9Zp91b_I5gr8LXvLDv7Ylez0aW7E'

# DEV
TELEGRAM_TOKEN = '6346978988:AAFIQ15EPGp56fDNzONyshwU2rgQ20KD36U'

# All handlers should be attached to the Router (or Dispatcher)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: types.Message):
    buttons = [
        types.KeyboardButton(text="/lms"),
        types.KeyboardButton(text="/support")
    ]
    markup = types.ReplyKeyboardMarkup(keyboard=[buttons])
    await message.answer('Выберите режим работы', reply_markup=markup)

async def main() -> None:
    # Initialize Bot instance with a default parse mode which will be passed to all API calls
    bot = Bot(TELEGRAM_TOKEN, parse_mode=ParseMode.HTML)

    dp.include_router(support_router)
    dp.include_router(lms_router)

    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())