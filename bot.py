from logic import DB_Manager
from config import *
from telebot import TeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telebot import types
from markups import *

user_states = {}
bot = TeleBot(token)
hideBoard = types.ReplyKeyboardRemove() 

manager = DB_Manager(DATABASE)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "all_comm":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "Выберите действие:", reply_markup=gen_markup_all_comm())
    
    elif call.data == "new_project":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        user_states[call.message.chat.id] = 'Gen_new_project'
        bot.send_message(call.message.chat.id, "Введите название проекта:")
        bot.register_next_step_handler(call.message, name_project)
    
    elif call.data == "skills":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        skill_handler(call.message)
    
    elif call.data == "projects":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        get_projects(call.message)
    
    elif call.data == "update_projects":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        update_project(call.message)
    
    elif call.data == "delete":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        delete_handler(call.message)
    
    elif call.data == "cancel":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        cansel(call.message)

        

cancel_button = "Отмена 🚫"

def cansel(message):
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=gen_markup_start())
  
def no_projects(message):
    bot.send_message(message.chat.id, 'У тебя пока нет проектов!', reply_markup=gen_markup_start())

def gen_inline_markup(rows):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    for row in rows:
        markup.add(InlineKeyboardButton(row, callback_data=f"project_{row}"))
    return markup

def gen_markup(rows):
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.row_width = 1
    for row in rows:
        markup.add(KeyboardButton(row))
    markup.add(KeyboardButton(cancel_button))
    return markup

attributes_of_projects = {
    'Имя проекта': ["Введите новое имя проекта", "project_name"],
    "Описание": ["Введите новое описание проекта", "description"],
    "Ссылка": ["Введите новую ссылку на проект", "url"],
    "Статус": ["Выберите новый статус задачи", "status_id"]
}

def info_project(message, user_id, project_name):
    info = manager.get_project_info(user_id, project_name)[0]
    skills = manager.get_project_skills(project_name)
    if not skills:
        skills = 'Навыки пока не добавлены'
    
    text = f"""Project name: {info[0]}
Description: {info[1]}
Link: {info[2]}
Status: {info[3]}
Skills: {skills}"""
    
    bot.send_message(message.chat.id, text, reply_markup=gen_markup_start())

@bot.message_handler(commands=['start'])
def start_command(message):
    bot.send_message(message.chat.id, """Привет! Я бот-менеджер проектов
Помогу тебе сохранить твои проекты и информацию о них!) 
""", reply_markup=gen_markup_start())

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    state = user_states.get(message.chat.id)
    
    if state == 'Gen_new_project':
        name_project(message)
    elif state == 'awaiting_project_name':
        name_project(message)
    else:
        # Проверяем, не является ли сообщение командой для существующего проекта
        user_id = message.from_user.id
        projects = [x[2] for x in manager.get_projects(user_id)]
        project = message.text
        
        if project in projects:
            info_project(message, user_id, project)
        else:
            bot.reply_to(message, "Тебе нужна помощь?", reply_markup=gen_markup_start())

def name_project(message):
    name = message.text
    user_id = message.from_user.id
    data = [user_id, name]
    bot.send_message(message.chat.id, "Введите ссылку на проект")
    bot.register_next_step_handler(message, link_project, data=data)

def link_project(message, data):
    data.append(message.text)
    statuses = [x[0] for x in manager.get_statuses()] 
    bot.send_message(message.chat.id, "Введите текущий статус проекта", reply_markup=gen_markup(statuses))
    bot.register_next_step_handler(message, callback_project, data=data, statuses=statuses)

def callback_project(message, data, statuses):
    status = message.text
    if message.text == cancel_button:
        cansel(message)
        user_states.pop(message.chat.id, None)
        return
    
    if status not in statuses:
        bot.send_message(message.chat.id, "Ты выбрал статус не из списка, попробуй еще раз!)", reply_markup=gen_markup(statuses))
        bot.register_next_step_handler(message, callback_project, data=data, statuses=statuses)
        return
    
    status_id = manager.get_status_id(status)
    data.append(status_id)
    manager.insert_project([tuple(data)])
    user_states.pop(message.chat.id, None)
    bot.send_message(message.chat.id, "Проект сохранен!", reply_markup=gen_markup_start())

def skill_handler(message):
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        projects = [x[2] for x in projects]
        bot.send_message(message.chat.id, 'Выбери проект для которого нужно добавить навык', reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, skill_project, projects=projects)
    else:
        no_projects(message)

def skill_project(message, projects):
    project_name = message.text
    if message.text == cancel_button:
        cansel(message)
        return
        
    if project_name not in projects:
        bot.send_message(message.chat.id, 'У тебя нет такого проекта, попробуй еще раз!)', reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, skill_project, projects=projects)
    else:
        skills = [x[1] for x in manager.get_skills()]
        bot.send_message(message.chat.id, 'Выбери навык', reply_markup=gen_markup(skills))
        bot.register_next_step_handler(message, set_skill, project_name=project_name, skills=skills)

def set_skill(message, project_name, skills):
    skill = message.text
    user_id = message.from_user.id
    if message.text == cancel_button:
        cansel(message)
        return
        
    if skill not in skills:
        bot.send_message(message.chat.id, 'Видимо, ты выбрал навык не из списка, попробуй еще раз!)', reply_markup=gen_markup(skills))
        bot.register_next_step_handler(message, set_skill, project_name=project_name, skills=skills)
        return
    
    manager.insert_skill(user_id, project_name, skill)
    bot.send_message(message.chat.id, f'Навык {skill} добавлен проекту {project_name}', reply_markup=gen_markup_start())

def get_projects(message):
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        text = "\n".join([f"Project name: {x[2]} \nLink: {x[4]}\n" for x in projects])
        bot.send_message(message.chat.id, text, reply_markup=gen_inline_markup([x[2] for x in projects]))
    else:
        no_projects(message)

def delete_handler(message):
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        projects_list = [x[2] for x in projects]
        text = "\n".join([f"Project name: {x[2]} \nLink: {x[4]}\n" for x in projects])
        bot.send_message(message.chat.id, text, reply_markup=gen_markup(projects_list))
        bot.register_next_step_handler(message, delete_project, projects=projects_list)
    else:
        no_projects(message)

def delete_project(message, projects):
    project = message.text
    user_id = message.from_user.id

    if message.text == cancel_button:
        cansel(message)
        return
    
    if project not in projects:
        bot.send_message(message.chat.id, 'У тебя нет такого проекта, попробуй выбрать еще раз!', reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, delete_project, projects=projects)
        return
    
    project_id = manager.get_project_id(project, user_id)
    manager.delete_project(user_id, project_id)
    bot.send_message(message.chat.id, f'Проект {project} удален!', reply_markup=gen_markup_start())

def update_project(message):
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        projects = [x[2] for x in projects]
        bot.send_message(message.chat.id, "Выбери проект, который хочешь изменить", reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, update_project_step_2, projects=projects)
    else:
        no_projects(message)

def update_project_step_2(message, projects):
    project_name = message.text
    if message.text == cancel_button:
        cansel(message)
        return
    
    if project_name not in projects:
        bot.send_message(message.chat.id, "Что-то пошло не так! Выбери проект еще раз:", reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, update_project_step_2, projects=projects)
        return
    
    bot.send_message(message.chat.id, "Выбери, что требуется изменить в проекте", reply_markup=gen_markup(attributes_of_projects.keys()))
    bot.register_next_step_handler(message, update_project_step_3, project_name=project_name)

def update_project_step_3(message, project_name):
    attribute = message.text
    if message.text == cancel_button:
        cansel(message)
        return
    
    if attribute not in attributes_of_projects.keys():
        bot.send_message(message.chat.id, "Кажется, ты ошибся, попробуй еще раз!", reply_markup=gen_markup(attributes_of_projects.keys()))
        bot.register_next_step_handler(message, update_project_step_3, project_name=project_name)
        return
    elif attribute == "Статус":
        rows = manager.get_statuses()
        bot.send_message(message.chat.id, attributes_of_projects[attribute][0], reply_markup=gen_markup([x[0] for x in rows]))
    else:
        bot.send_message(message.chat.id, attributes_of_projects[attribute][0])
    
    bot.register_next_step_handler(message, update_project_step_4, project_name=project_name, attribute=attributes_of_projects[attribute][1])

def update_project_step_4(message, project_name, attribute): 
    update_info = message.text
    if attribute == "status_id":
        rows = manager.get_statuses()
        if update_info in [x[0] for x in rows]:
            update_info = manager.get_status_id(update_info)
        elif update_info == cancel_button:
            cansel(message)
            return
        else:
            bot.send_message(message.chat.id, "Был выбран неверный статус, попробуй еще раз!", reply_markup=gen_markup([x[0] for x in rows]))
            bot.register_next_step_handler(message, update_project_step_4, project_name=project_name, attribute=attribute)
            return
    
    user_id = message.from_user.id
    data = (update_info, project_name, user_id)
    manager.update_projects(attribute, data)
    bot.send_message(message.chat.id, "Готово! Обновления внесены!", reply_markup=gen_markup_start())

if __name__ == '__main__':
    bot.infinity_polling()
