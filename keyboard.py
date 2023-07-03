from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton

start = InlineKeyboardMarkup(
    ).add(
        InlineKeyboardButton("💎 Профиль", callback_data='profile'),
        InlineKeyboardButton("💸 Пополнить баланс", callback_data='bur')
    ).add(
        InlineKeyboardButton("💬 Чат техподдержки", url='https://t.me/SakuraHostChats')
    )

text_start_menu = InlineKeyboardMarkup(row_width=2)
crypto = InlineKeyboardButton("💎 CryptoBot", callback_data='cryptobot')
ru = InlineKeyboardButton("💳 Карта RU", callback_data='ru')
bask = InlineKeyboardButton("🔙 Назад", callback_data='start')
text_start_menu.add(crypto, ru, bask)


oplata = InlineKeyboardMarkup(row_width=1)
oplata_crypto = InlineKeyboardButton("💸 Оплатить", url='http://t.me/CryptoBot?start=IV8PrX7IP4Mk')
ba = InlineKeyboardButton("🔙 Назад", callback_data='bur')
oplata.add(oplata_crypto, ba)

text_start_r = InlineKeyboardMarkup(row_width=1)
ba = InlineKeyboardButton("🔙 Назад", callback_data='bur')
text_start_r.add(ba)

back = InlineKeyboardMarkup(
    ).add(
        InlineKeyboardButton("🔙 Назад", callback_data='start')
    )
