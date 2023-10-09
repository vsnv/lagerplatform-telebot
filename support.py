from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram import types

from aiogram import Router

from aiogram.filters import (
    Command,
    CommandObject,
    ExceptionMessageFilter,
    ExceptionTypeFilter,
)

support_router = Router()

@support_router.message(Command("support"))
async def support(message: types.Message):
    await message.answer('В чем суть проблемы? Опишите как можно детальнее и администратор обязательно вам ответит.', reply_markup=ReplyKeyboardRemove())

#
# @support_router.message_handler(state=SosState.question)
# async def process_question(message: Message, state: FSMContext):
#     async with state.proxy() as data:
#         data['question'] = message.text
#
#     await message.answer('Убедитесь, что все верно.', reply_markup=submit_markup())
#     await SosState.next()
#
#
# @support_router.message_handler(lambda message: message.text not in [cancel_message, all_right_message], state=SosState.submit)
# async def process_price_invalid(message: Message):
#     await message.answer('Такого варианта не было.')
#
#
# @support_router.message_handler(text=cancel_message, state=SosState.submit)
# async def process_cancel(message: Message, state: FSMContext):
#     await message.answer('Отменено!', reply_markup=ReplyKeyboardRemove())
#     await state.finish()
#
#
# @support_router.message_handler(text=all_right_message, state=SosState.submit)
# async def process_submit(message: Message, state: FSMContext):
#
#     cid = message.chat.id
#
#     if db.fetchone('SELECT * FROM questions WHERE cid=?', (cid,)) == None:
#
#         async with state.proxy() as data:
#             db.query('INSERT INTO questions VALUES (?, ?)',
#                      (cid, data['question']))
#
#         await message.answer('Отправлено!', reply_markup=ReplyKeyboardRemove())
#
#     else:
#
#         await message.answer('Превышен лимит на количество задаваемых вопросов.', reply_markup=ReplyKeyboardRemove())
#
#     await state.finish()