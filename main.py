import telebot
import logging
from notion_client import Client
from pprint import pprint
from telebot import types
import json
import re

notion = Client(auth="secret_v9RLCFDR8ld1pX4sOeoSNoDcG6dNh27RhfOFmHUAE9u")

# Конфигурация
TELEGRAM_TOKEN = '6302082234:AAF_5Mi9Zp91b_I5gr8LXvLDv7Ylez0aW7E'
# NOTION_TOKEN = 'secret_v9RLCFDR8ld1pX4sOeoSNoDcG6dNh27RhfOFmHUAE9u'

#https://modern-yamamomo-891.notion.site/bb566392aa724e02946023feeae3d1b9?pvs=4

bot = telebot.TeleBot(TELEGRAM_TOKEN)

main_page_id = "ecb3df35eb554c329fd1ed3aea697ec8"

current_question_index = -1
correct_answers_count = {}

@bot.message_handler(commands=['start'])
def start(message):
    send_child_pages(message.chat.id, main_page_id)

@bot.callback_query_handler(func=lambda call: json.loads(call.data).get("t") == "c")
def callback_inline(call):
    data = json.loads(call.data)
    child_id = data["p"]
    send_child_pages(call.message.chat.id, child_id)

@bot.callback_query_handler(func=lambda call: json.loads(call.data).get("t") == "t")
def callback_another_action(call):
    global current_question_index
    data = json.loads(call.data)
    page_id = data["p"]
    # Здесь вы можете добавить обработку ответа, например, записать его куда-то или проверить, правильный ли он

    questions = parse_page(page_id)
    current_question_index += 1
    if current_question_index < len(questions):
        send_question(call.message.chat.id, page_id, questions)
    else:
        current_question_index = -1
        bot.send_message(call.message.chat.id, "Спасибо за участие в опросе!")

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
            callback_data = {
                "t": "c",
                "p": child["id"]
            }
            button = types.InlineKeyboardButton(text=title, callback_data=json.dumps(callback_data))
            markup.add(button)
        else:
            if child["child_page"]["title"].startswith("📝"):
                callback_data = {
                    "t": "t",
                    "p": child["id"],
                    "d": 0
                }
                markup.add(types.InlineKeyboardButton(text=title, callback_data=json.dumps(callback_data)))
            else:
                notion_url = f"https://www.notion.so/{child['id'].replace('-', '')}"
                button = types.InlineKeyboardButton(text=title, url=notion_url)
                markup.add(button)
    bot.send_message(chat_id, text_content, reply_markup=markup)

def parse_page(page_id):
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

def send_question(chat_id, page_id, questions):
    markup = types.InlineKeyboardMarkup()
    for answer in questions[current_question_index]['answers']:
        callback_data = {
            "t": "t",
            "p": page_id
        }
        markup.add(types.InlineKeyboardButton(text=answer['text'], callback_data=json.dumps(callback_data)))
    bot.send_message(chat_id, questions[current_question_index]['text'], reply_markup=markup)


# def send_question(chat_id, questions):
#     index = current_question_index[chat_id]
#     question = questions[index]
#     markup = types.InlineKeyboardMarkup()
#     for i, answer in enumerate(question["answers"]):
#         markup.add(types.InlineKeyboardButton(text=answer["text"], callback_data=str(i)))
#     bot.send_message(chat_id, question["text"], reply_markup=markup)

# @bot.callback_query_handler(func=lambda call: True)
# def on_answer_selected(call):
#     index = current_question_index[call.message.chat.id]
#     answer = questions[index]["answers"][int(call.data)]
#
#     if answer["is_correct"]:
#         correct_answers_count[call.message.chat.id] += 1
#
#     current_question_index[call.message.chat.id] += 1
#     if current_question_index[call.message.chat.id] < len(questions):
#         send_question(call.message.chat.id, questions)
#     else:
#         send_test_result(call.message.chat.id)

# def send_test_result(chat_id):
#     result = f"Вы правильно ответили на {correct_answers_count[chat_id]} из {len(questions)} вопросов."
#     bot.send_message(chat_id, result)

bot.infinity_polling()
