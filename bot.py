import telebot
from telebot import types
import requests
import config
from db import UserScore, Questions, CustomPath, delete_old_questions, update_user_score, get_last_info, update_last_info

# define bot
bot = telebot.TeleBot(config.TOKEN)

instruction =  """When you start, bot sends you a message with three question categories. 
\nYou can choose one of them, then bot sends you a question.
\nAfter you decide, you can click on the button 'Answer' to see the correct answer for the selected question.
\nSo that you need to choose were you right or not.
\nAfter that you gonna see how many points you earned.
\nWhen you click on the button 'End the game' the game will be finished and you will see your final score:)
\nYou can always get another question by clicking on the button 'Next question'
\nGood luck!"""

# function than dawnload questions and get user to choose category
def choose_category(message):
    BASE_URL = 'http://jservice.io/api/random'
    categories = []
    ids = []
    for i in range(3):
        response = requests.get(f"{BASE_URL}")
        data = response.json()
        q_id = data[0]['id']
        question = data[0]['question']
        answer = data[0]['answer']
        if data[0]['value'] is None:
            price = 1000
        else:
            price = int(data[0]['value'])
        category = data[0]['category']['title']
        categories.append(category)
        ids.append(q_id)
        Questions.create(question=question, answer=answer, price=price, category=category, user_id=message.from_user.id, q_id=q_id)

    inl_markup = types.InlineKeyboardMarkup(row_width=1)
    inl_item1= types.InlineKeyboardButton(categories[0], callback_data=('question_'+str(ids[0])))
    inl_item2= types.InlineKeyboardButton(categories[1], callback_data=('question_'+str(ids[1])))
    inl_item3= types.InlineKeyboardButton(categories[2], callback_data=('question_'+str(ids[2])))
    inl_markup.add(inl_item1, inl_item2, inl_item3)
    bot.send_message(message.chat.id, 'Choose the category:', reply_markup=inl_markup)

# function that draw standart game buttons ('Next question' and 'End the game')
def standart_game_buttons(message, question):

    rep_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    rep_item1 = types.KeyboardButton('Next question')
    rep_item2 = types.KeyboardButton('End the game')
    rep_markup.add(rep_item1, rep_item2)
    bot.send_message(chat_id=message.chat.id, text='Question: ' + question, reply_markup=rep_markup)

    inl_markup = types.InlineKeyboardMarkup(row_width=2)
    inl_item= types.InlineKeyboardButton('Get the answer', callback_data='answer')
    inl_markup.add(inl_item)
    bot.send_message(chat_id=message.chat.id, text='Click to get the answer', reply_markup=inl_markup)

# start message hendler
@bot.message_handler(commands=['start'])
def send_welcome(message):

    rep_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    rep_item = types.KeyboardButton('Start the game')
    rep_markup.add(rep_item)
    hello_text = 'Hello :) I am a quize bot! I can ask you questions and calculate your game score!'
    bot.send_message(chat_id=message.chat.id, text=hello_text, reply_markup=rep_markup)

    inl_markup = types.InlineKeyboardMarkup(row_width=1)
    instruction_text = 'Rules are very simple! Just start the game ;) \nBut if you want to see the unstruiction - click the button below. Also, you always can text command /help for help :)'
    inl_item= types.InlineKeyboardButton('Instruction', callback_data=('instruction'))
    inl_markup.add(inl_item)
    bot.send_message(message.chat.id, instruction_text, reply_markup=inl_markup)

# help message hendler
@bot.message_handler(commands=['help'])
def send_welcome(message):

    inl_markup = types.InlineKeyboardMarkup(row_width=1)
    instruction_text = 'Rules are very simple! Just start the game ;) \nBut if you want to see the unstruiction - click the button below.'
    inl_item= types.InlineKeyboardButton('Instruction', callback_data=('instruction'))
    inl_markup.add(inl_item)
    bot.send_message(message.chat.id, instruction_text, reply_markup=inl_markup)

# message hendler
@bot.message_handler(content_types=['text'])
def lalala(message):

    if message.text == 'Start the game':
        update_user_score(UserScore, message.from_user.id, 0)
        choose_category(message)

    elif message.text == 'Next question':
        delete_old_questions(Questions, message.from_user.id)
        choose_category(message)

    elif message.text == 'End the game':
        rep_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        rep_item = types.KeyboardButton('Start the game')
        rep_markup.add(rep_item)
        score = UserScore.get(UserScore.user_id==message.from_user.id).score  
        query = UserScore.delete().where(UserScore.user_id == message.from_user.id)
        query.execute()
        bot.send_message(chat_id=message.chat.id, text='Your final score: ' + str(score) + ' points!', reply_markup=rep_markup)

    else:
        bot.send_message(chat_id=message.chat.id, text='Sorry, I do not know this command. You can write /help for help.')

# callback handler
@bot.callback_query_handler(func=lambda call:True)
def callback_inline(call):

    if call.data == 'instruction':
        bot.send_message(call.message.chat.id, instruction)
        buttom_text = 'Instruction:'

    elif call.data[:8] == 'question':
        q_info = Questions.get(Questions.q_id==int(call.data[9:]))
        price = q_info.price
        question = q_info.question
        answer = q_info.answer
        delete_old_questions(Questions, call.from_user.id)
        update_last_info(CustomPath, call.from_user.id, answer, price)
        standart_game_buttons(call.message, question)
        buttom_text = 'Price ' + str(price) + ':'

    elif call.data == 'answer':
        li = get_last_info(CustomPath, call.from_user.id)
        inl_markup = types.InlineKeyboardMarkup(row_width=2)
        inl_item1 = types.InlineKeyboardButton('I was right!', callback_data=('was_right'))
        inl_item2 = types.InlineKeyboardButton('I was wrong!', callback_data=('was_wrong'))
        inl_markup.add(inl_item1, inl_item2)
        bot.send_message(call.message.chat.id, 'Were you right?', reply_markup=inl_markup)
        buttom_text = 'Answer: ' + li.answer

    elif call.data[:3] == 'was':
        if call.data == 'was_wrong':
            price = 0
            buttom_text = 'Sorry, you do not gain any points :('
        else:
            price = CustomPath.get(CustomPath.user_id == call.from_user.id).price
            buttom_text = 'Congradulations, you have reached ' + str(price) + ' points!'
        update_user_score(UserScore, call.from_user.id, price)

    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=buttom_text, reply_markup=None)

# stop handler
bot.infinity_polling(timeout=10, long_polling_timeout = 5)
