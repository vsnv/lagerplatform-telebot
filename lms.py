import json
import re

from notion_client import Client

from aiogram import Router
from aiogram import F
from aiogram import types
from aiogram.types import FSInputFile, URLInputFile, BufferedInputFile
from typing import Optional
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder

from aiogram.filters import (
    Command,
    CommandObject,
    ExceptionMessageFilter,
    ExceptionTypeFilter,
)

NOTION_TOKEN = 'secret_v9RLCFDR8ld1pX4sOeoSNoDcG6dNh27RhfOFmHUAE9u'

notion = Client(auth="secret_v9RLCFDR8ld1pX4sOeoSNoDcG6dNh27RhfOFmHUAE9u")

lms_page_id = "ecb3df35eb554c329fd1ed3aea697ec8"

current_question_index = -1

lms_router = Router()

from typing import Optional
from aiogram.filters.callback_data import CallbackData

class LMSCallbackFactory(CallbackData, prefix="lms"):
    action: str
    page_id: str

@lms_router.message(Command("lms"))
async def lms(message):
    await send_child_pages(message, message.chat.id, lms_page_id)

@lms_router.callback_query(LMSCallbackFactory.filter(F.action == "category"))
async def callback_category(
    callback: types.CallbackQuery,
    callback_data: LMSCallbackFactory
):
    await send_child_pages(callback.message, callback.message.chat.id, callback_data.page_id)

@lms_router.callback_query(LMSCallbackFactory.filter(F.action == "test"))
async def callback_test(
    callback: types.CallbackQuery,
    callback_data: LMSCallbackFactory
):
    global current_question_index

    message = callback.message
    page_id = callback_data.page_id

    questions = await parse_page(page_id)
    current_question_index += 1
    if current_question_index < len(questions):
        await send_question(message, page_id, questions)
    else:
        current_question_index = -1
        await message.answer("Спасибо за участие в опросе!")

async def send_child_pages(message, chat_id, parent_page_id):
    builder = InlineKeyboardBuilder()

    children = notion.blocks.children.list(block_id=parent_page_id)

    has_image = False

    text_content = ""
    for child in children["results"]:
        if child["type"] == "paragraph" and child["paragraph"].get("text"):
            text_content += child["paragraph"]["text"][0].get("plain_text", "") + '\n\n'
        elif child["type"] == "paragraph" and "rich_text" in child["paragraph"]:
            for text_segment in child["paragraph"]["rich_text"]:
                text_content += text_segment.get("plain_text", "")
            text_content += '\n'
        elif child["type"] == "image" and not has_image:  # отправляем только первое изображение
            image_url = child["image"]["file"]["url"]
            image_from_url = URLInputFile(image_url)
            await message.answer_photo(
                image_from_url
            )
            # bot.send_photo(chat_id, image_url)
            has_image = True

    message_text = text_content if text_content else "Выберите страницу:"

    child_pages = [child for child in children["results"] if child["type"] == "child_page"]

    for child in child_pages:
        title = child["child_page"]["title"]

        grand_children = notion.blocks.children.list(block_id=child["id"])
        grand_child_pages = [gchild for gchild in grand_children["results"] if gchild["type"] == "child_page"]

        if grand_child_pages:
            callback_data = {
                "t": "c",
                "p": child["id"]
            }
            builder.button(
                text=title,
                callback_data=LMSCallbackFactory(
                    action="category",
                    page_id=child["id"]
                )
            )
        else:
            if child["child_page"]["title"].startswith("📝"):
                builder.button(
                    text=title,
                    callback_data=LMSCallbackFactory(
                        action="test",
                        page_id=child["id"]
                    )
                )
            else:
                notion_url = f"https://www.notion.so/{child['id'].replace('-', '')}"
                builder.button(text=title, url=notion_url)
    builder.adjust(1)
    await message.answer(message_text, reply_markup=builder.as_markup(resize_keyboard=True))

async def parse_page(page_id):
    children = notion.blocks.children.list(page_id)["results"]
    questions = []
    for child in children:
        if child["type"] == "heading_1":
            question_text = child["heading_1"]["rich_text"][0]["plain_text"]
            questions.append({"text": question_text, "answers": []})
        elif child["type"] == "bulleted_list_item":
            answer_text = child["bulleted_list_item"]["rich_text"][0]["plain_text"]
            is_correct = answer_text.endswith('*')
            questions[-1]["answers"].append({"text": re.sub(r'\*$', '', answer_text), "is_correct": is_correct})
    return questions

async def send_question(message: types.Message, page_id, questions):
    builder = InlineKeyboardBuilder()
    for answer in questions[current_question_index]['answers']:
        callback_data = {
            "t": "t",
            "p": page_id
        }
        builder.button(
            text=answer['text'],
            callback_data=LMSCallbackFactory(
                action="test",
                page_id=page_id
            )
        )
    builder.adjust(1)
    await message.answer(questions[current_question_index]['text'], reply_markup=builder.as_markup())
