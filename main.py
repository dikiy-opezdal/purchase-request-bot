import logging
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ContextTypes,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    PicklePersistence,
    CallbackQueryHandler,
)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


requests_chat_id = open('data/requests_chat_id.txt', 'r').read()

commands_keyboard_markup = ReplyKeyboardMarkup(
    [['Запит на покупку']],
    one_time_keyboard=True
)

confirmation_keyboard_markup = ReplyKeyboardMarkup(
    [['Так', 'Ні']],
    one_time_keyboard=True
)

request_keyboard =\
[
    [
        InlineKeyboardButton('Відхилити'),
        InlineKeyboardButton('Відповісти')
    ],
    [InlineKeyboardButton('Профіль')]
]

NAME, PRICE, REASON, DESCRIPTION, CONFIRM, END = range(6)

REQUESTS_DATA = 0
USERID_DATA, USERFIRSTNAME_DATA, USERNAME_DATA, NAME_DATA, PRICE_DATA, REASON_DATA, DESCRIPTION_DATA, LAST_REQUEST_REPLY_DATA = range(8)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(text='Привіт! Я допоможу тобі робити запити на покупки речей. Вибери одну з доступних команд для початку.', parse_mode=ParseMode.HTML, reply_markup=commands_keyboard_markup)


async def product_name_state(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(text='Введіть назву товару. /cancel для відміни запиту')

    return NAME

async def product_price_state(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data[NAME_DATA] = update.message.text
    await update.message.reply_text(text='Введіть вартість товару.')

    return PRICE

async def purchase_reason_state(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data[PRICE_DATA] = update.message.text
    await update.message.reply_text(text='Чому ми повинні придбати цей товар?')

    return REASON

async def description_state(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data[REASON_DATA] = update.message.text
    await update.message.reply_text(text='Вкажіть будь-яку додаткову інформацію. /skip для пропуску')

    return DESCRIPTION

async def skip_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data[DESCRIPTION_DATA] = None
    await update.message.reply_text(text=f'Назва: <b>{context.user_data.get(NAME_DATA)}</b>\nЦіна: <b>{context.user_data.get(PRICE_DATA)}</b>\nПричина покупки: <b>{context.user_data.get(REASON_DATA)}</b>\n\nВсе вірно?', parse_mode=ParseMode.HTML, reply_markup=confirmation_keyboard_markup)

    return CONFIRM

async def confirm_state(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data[DESCRIPTION_DATA] = update.message.text
    await update.message.reply_text(text=f'Назва: <b>{context.user_data.get(NAME_DATA)}</b>\nЦіна: <b>{context.user_data.get(PRICE_DATA)}</b>\nПричина покупки: <b>{context.user_data.get(REASON_DATA)}</b>\nДодаткова інформація: <b>{context.user_data.get(DESCRIPTION_DATA)}</b>\n\nВсе вірно?', parse_mode=ParseMode.HTML, reply_markup=confirmation_keyboard_markup)

    return CONFIRM

async def end_state(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    answer = update.message.text
    if answer == 'Так':
        description = ''
        username = ''
        if context.user_data.get(DESCRIPTION_DATA):
            description = f'\nДодаткова інформація: <b>{context.user_data.get(DESCRIPTION_DATA)}</b>'
        if update.message.from_user.username:
            username = f'(@{update.message.from_user.username})'
        request_keyboard[0][0] = InlineKeyboardButton('Відхилити', callback_data=f'-{len(context.bot_data.get(REQUESTS_DATA) or [])}')
        request_keyboard[0][1] = InlineKeyboardButton('Відповісти', callback_data=f'{len(context.bot_data.get(REQUESTS_DATA) or [])}')
        request_keyboard[1][0] = InlineKeyboardButton('Профіль', url=f'tg://user?id={update.message.from_user.id}')
        if not REQUESTS_DATA in context.bot_data:
            context.bot_data[REQUESTS_DATA] = []
        context.bot_data.get(REQUESTS_DATA).append([update.message.from_user.id, update.message.from_user.first_name, username, context.user_data.get(NAME_DATA), context.user_data.get(PRICE_DATA), context.user_data.get(REASON_DATA), context.user_data.get(DESCRIPTION_DATA)])
        await context.bot.send_message(chat_id=requests_chat_id, text=f'Отримано запит на покупку товару від {update.message.from_user.first_name}{username}:\n\nНазва: <b>{context.user_data.get(NAME_DATA)}</b>\nЦіна: <b>{context.user_data.get(PRICE_DATA)}</b>\nПричина покупки: <b>{context.user_data.get(REASON_DATA)}</b>{description}', parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(request_keyboard))
        await update.message.reply_text(text=f'Запит відправлено({len(context.bot_data.get(REQUESTS_DATA))-1}). Очікуйте на відповідь адміністратора.', reply_markup=commands_keyboard_markup)
    elif answer == 'Ні':
        await update.message.reply_text(text='Запит відмінено.', reply_markup=commands_keyboard_markup)

    return ConversationHandler.END

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(text='Відмінено.', reply_markup=commands_keyboard_markup)

    return ConversationHandler.END


async def deny_CallbackQuery(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    request_id = abs(int(query.data))

    await context.bot.send_message(chat_id=context.bot_data[REQUESTS_DATA][request_id][USERID_DATA], text=f'Ваш запит({request_id}) було відхилено.')
    description = ''
    if context.bot_data[REQUESTS_DATA][request_id][DESCRIPTION_DATA]:
        description = f'\nДодаткова інформація: <b>{context.bot_data[REQUESTS_DATA][request_id][DESCRIPTION_DATA]}</b>'
    await query.edit_message_text(text=f'Запит на покупку товару від {context.bot_data[REQUESTS_DATA][request_id][USERFIRSTNAME_DATA]}{context.bot_data[REQUESTS_DATA][request_id][USERNAME_DATA]}:\n\nНазва: <b>{context.bot_data[REQUESTS_DATA][request_id][NAME_DATA]}</b>\nЦіна: <b>{context.bot_data[REQUESTS_DATA][request_id][PRICE_DATA]}</b>\nПричина покупки: <b>{context.bot_data[REQUESTS_DATA][request_id][REASON_DATA]}</b>{description}\n\n<b>Відхилено</b>', parse_mode=ParseMode.HTML, reply_markup=None)


async def forward_CallbackQuery(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    request_id = abs(int(query.data))

    description = ''
    if context.bot_data[REQUESTS_DATA][request_id][DESCRIPTION_DATA]:
        description = f'\nДодаткова інформація: <b>{context.bot_data[REQUESTS_DATA][request_id][DESCRIPTION_DATA]}</b>'
    await query.edit_message_text(text=f'Запит на покупку товару від {context.bot_data[REQUESTS_DATA][request_id][USERFIRSTNAME_DATA]}{context.bot_data[REQUESTS_DATA][request_id][USERNAME_DATA]}:\n\nНазва: <b>{context.bot_data[REQUESTS_DATA][request_id][NAME_DATA]}</b>\nЦіна: <b>{context.bot_data[REQUESTS_DATA][request_id][PRICE_DATA]}</b>\nПричина покупки: <b>{context.bot_data[REQUESTS_DATA][request_id][REASON_DATA]}</b>{description}\n\n<b>Відправлено відповідь</b>', parse_mode=ParseMode.HTML, reply_markup=None)
    await context.bot.send_message(chat_id=update.callback_query.from_user.id, text='Напишіть текст відповіді.')
    context.user_data[LAST_REQUEST_REPLY_DATA] = request_id

    return 0

async def forward_message_state(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    request_id = context.user_data[LAST_REQUEST_REPLY_DATA]
    await context.bot.send_message(chat_id=context.bot_data[REQUESTS_DATA][request_id][USERID_DATA], text=f'На ваш запит({request_id}) відправлено відповідь:\n\n{update.message.text}')
    await update.message.reply_text(text='Відповідь відправлено.')

    return ConversationHandler.END


def main() -> None:
    application = Application.builder().token(open('data/token.txt', 'r').read()).build()

    application.bot_data[REQUESTS_DATA] = []

    application.add_handler(CommandHandler('start', start_command))

    application.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Запит на покупку$'), product_name_state)],
        states={
            NAME: [MessageHandler(filters.Regex(r'^(?!.*\/cancel).*'), product_price_state)],
            PRICE: [MessageHandler(filters.Regex(r'^(?!.*\/cancel).*'), purchase_reason_state)],
            REASON: [MessageHandler(filters.Regex(r'^(?!.*\/cancel).*'), description_state)],
            DESCRIPTION: [
                MessageHandler(filters.Regex(r'^(?!.*\/(cancel|skip)).*'), confirm_state),
                CommandHandler('skip', skip_description)
            ],
            CONFIRM: [MessageHandler(filters.Regex('^(Так|Ні)$'), end_state)]
        },
        fallbacks=[CommandHandler('cancel', cancel_command)]
    ))

    application.add_handler(CallbackQueryHandler(deny_CallbackQuery, pattern=r'^-'))
    application.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(forward_CallbackQuery, pattern=r'^\d')],
        states={
            0: [MessageHandler(filters.Regex(r'^(?!.*\/cancel).*'), forward_message_state)]
        },
        fallbacks=[CommandHandler('cancel', cancel_command)]
    ))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()