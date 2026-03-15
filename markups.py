from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def create_inline_markup_1(buttons):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(*buttons)
    return markup


def gen_markup_start():
        buttons = [InlineKeyboardButton('⭐Узнать все команды⭐', callback_data='all_comm')]
        return create_inline_markup_1(buttons)


def gen_markup_all_comm():
        buttons = [InlineKeyboardButton('Создать проект', callback_data='new_project'),
                   InlineKeyboardButton('Добавить навык', callback_data='skills'),
                   InlineKeyboardButton('Инфа о проекте', callback_data='projects'),
                   InlineKeyboardButton('Изменить проект', callback_data='update_projects'),
                   InlineKeyboardButton('Удалить проект', callback_data='delete')]
        return create_inline_markup_1(buttons)
