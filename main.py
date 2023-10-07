import telebot
import logging
from notion_client import Client
from pprint import pprint
from telebot import types

notion = Client(auth="secret_v9RLCFDR8ld1pX4sOeoSNoDcG6dNh27RhfOFmHUAE9u")

# Конфигурация
TELEGRAM_TOKEN = '6302082234:AAF_5Mi9Zp91b_I5gr8LXvLDv7Ylez0aW7E'
# NOTION_TOKEN = 'secret_v9RLCFDR8ld1pX4sOeoSNoDcG6dNh27RhfOFmHUAE9u'

#https://modern-yamamomo-891.notion.site/bb566392aa724e02946023feeae3d1b9?pvs=4

bot = telebot.TeleBot(TELEGRAM_TOKEN)

main_page_id = "ecb3df35eb554c329fd1ed3aea697ec8"

@bot.message_handler(commands=['start'])
def start(message):
    send_child_pages(message.chat.id, main_page_id)

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    send_child_pages(call.message.chat.id, call.data)

def send_child_pages(chat_id, parent_page_id):
    markup = types.InlineKeyboardMarkup()

    children = notion.blocks.children.list(block_id=parent_page_id)

    has_image = False  # Флаг для проверки наличия изображения

    # Собираем текст из текстовых блоков
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
            bot.send_photo(chat_id, image_url)
            has_image = True

    # Если у страницы есть текстовые блоки, добавим их к сообщению
    message_text = text_content if text_content else "Выберите страницу:"

    child_pages = [child for child in children["results"] if child["type"] == "child_page"]

    for child in child_pages:
        title = child["child_page"]["title"]

        # Проверяем дочерние страницы этой дочерней страницы
        grand_children = notion.blocks.children.list(block_id=child["id"])
        grand_child_pages = [gchild for gchild in grand_children["results"] if gchild["type"] == "child_page"]

        # Если у дочерней страницы есть свои дочерние страницы
        if grand_child_pages:
            button = types.InlineKeyboardButton(text=title, callback_data=child["id"])
        else:
            notion_url = f"https://www.notion.so/{child['id'].replace('-', '')}"
            button = types.InlineKeyboardButton(text=title, url=notion_url)

        markup.add(button)

    bot.send_message(chat_id, text_content, reply_markup=markup)

bot.infinity_polling()