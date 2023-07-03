import logging
import asyncio
from config import *
from config import admin
from keyboard import *
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from db import join
import sqlite3
import SDocker as dckr

bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

connection = sqlite3.connect('data.db')
q = connection.cursor()

logging.basicConfig(level=logging.INFO)

async def decrease_days():
    while True:
        connection = sqlite3.connect('data.db')
        cursor = connection.cursor()

        cursor.execute('SELECT user_id, days FROM users')
        users = cursor.fetchall()

        for user in users:
            user_id, days = user
            if days > 0:
                days -= 1
                cursor.execute('UPDATE users SET days = ? WHERE user_id = ?', (days, user_id))
                if days == 0:
                    await bot.send_message(5964924297, f"<b>У пользователя с айди [<code>{user_id}</code>] закончились дни подписки.</b>")
                    await bot.send_message(int(user_id), f"<b>❗️Закончились дни подписки, продлите хостинг.</b>")

        connection.commit()
        connection.close()

        await asyncio.sleep(24 * 60 * 60)

@dp.callback_query_handler(text='install')
async def install_call(call):
   balanc = q.execute(f"SELECT balance FROM users WHERE user_id = {call.from_user.id}")
   balance = balanc.fetchone()[0]
   
   if balance < 45:
      return await call.answer(f"❌ Не достачно средств на балансе!\nМинимум 45₽", show_alert=True)
   
   q.execute("UPDATE users SET balance = ? WHERE user_id = ?", (balance-45, call.from_user.id))
   connection.commit()
   q.execute(f"SELECT days FROM users WHERE user_id = {call.from_user.id}")
   days = q.fetchone()[0]
   q.execute("UPDATE users SET days = ? WHERE user_id = ?", (days+30, call.from_user.id))
   connection.commit()
   await call.message.edit_text(f"<i>Ожидайте ссылку...</i>")

@dp.message_handler(commands=['setdays'])
async def send_message(message: types.Message):
  if message.from_user.id == admin:
    days = int(message.text.split(maxsplit=2)[2])
    id = message.text.split(maxsplit=2)[1]
    q.execute(f"SELECT * FROM users WHERE user_id = {id}")
    result = q.fetchall()
    if len(result) == 0:
        return await message.reply(f"<
        \b>Пользователя с айди</b> [<code>{id}<code>] <b>нет в базе, он должен написать <code>/start</code> боту</b>")
    q.execute("UPDATE users SET days = ? WHERE user_id = ?", (days, id))
    connection.commit()
    await message.reply(f"<b>Успешно обновил дни пользователю с айди</b> [<code>{id}</code>]")

@dp.message_handler(commands=['install'])
async def install(m: types.Message):
    if butils.bignore(m.from_user):
        return

    await suspend(m)

    tds = TDS(m.from_user)

    if not op.get_user(str(m.from_user.id), 'activated'):
        return await m.answer(tds.get('no_subscription_e'))

    nm = await m.answer(tds.get('await_0'))
    try:
        datab = json.load(open('haupt.json', 'r', encoding='utf-8'))
        ports: tuple = tuple(datab[user]['port'] for user in datab.keys())
        port = random.randint(48001, 49200)
        while port in ports or port in PORTS_FORBIDDEN:
                port = random.randint(48003, 49200)
        op.edit_user(str(m.from_user.id), 'port', str(port))

        while True:
            try:
                dckr.create(port, str(m.from_user.id))
                break
            except dckr.docker.errors.APIError as e:
                text = str(e)
                if 'port is already allocated' in text:
                    port = random.randint(48001, 49200)
                    while port in ports or port in PORTS_FORBIDDEN:
                        port = random.randint(48001, 49200)
                    op.edit_user(str(m.from_user.id), 'port', str(port))
                else:
                    raise e
        
        addr = dckr.cmodel['ip'] + op.get_user(str(m.from_user.id), 'port')
        await nm.delete()
        keyb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyb.add(types.KeyboardButton(text=tds.get('start_button')), types.KeyboardButton(text=tds.get('stop_button')))
        keyb.add(types.KeyboardButton(text=tds.get('restart_button')))
        await m.reply(tds.get('login_message').format(addr, tds.get('privacy_alert')), reply_markup=keyb)
        op.edit_user(str(m.from_user.id), 'installed', True)
    except dckr.docker.errors.APIError as e:
        error_description = f'{tds.get("possible_cause", additional_file="e").format(tds.get("DockerAlreadyExists", additional_file="e"))}'
        await nm.edit_text(f"{tds.get('proc_err')}\n{error_description}")
        logging.error(e)
    except Exception as e:
        await nm.edit_text(tds.get('proc_err') + f'\n<code>{e}</>')

@dp.message_handler(lambda m: m.text[:2] == '▶ ' or m.text == '/run')
async def start(m: types.Message):
    if butils.bignore(m.from_user):
        return

    await suspend(m)

    tds = TDS(m.from_user)

    nm = await m.answer(tds.get('starting'))
    try:
        dckr.start(str(m.from_user.id))
        await nm.edit_text(tds.get('proc_done'))
    except dckr.docker.errors.NotFound as e:
        error_description = f'{tds.get("possible_cause", additional_file="e").format(tds.get("DockerNotFound", additional_file="e"))}'
        await nm.edit_text(f"{tds.get('proc_err')}\n{error_description}")
        logging.error(e)
    except dckr.docker.errors.APIError as e:
        error_description = f'{tds.get("possible_cause", additional_file="e").format(tds.get("DockerAlreadyExists", additional_file="e"))}'
        await nm.edit_text(f"{tds.get('proc_err')}\n{error_description}")
        logging.error(e)
    except Exception as e:
        await nm.edit_text(tds.get('proc_err') + f'\n<code>{e}</>')
        logging.error(e)
        
        @dp.message_handler(lambda m: m.text[:2] == '🔄 ' or m.text == '/restart')
async def refresh(m: types.Message):
    if butils.bignore(m.from_user):
        return

    await suspend(m)

    tds = TDS(m.from_user)

    nm = await m.answer(tds.get('restarting'))
    try:
        await dckr.restart(str(m.from_user.id))
        await nm.edit_text(tds.get('proc_done'))
    except dckr.docker.errors.NotFound as e:
        error_description = f'{tds.get("possible_cause", additional_file="e").format(tds.get("DockerNotFound", additional_file="e"))}'
        await nm.edit_text(f"{tds.get('proc_err')}\n{error_description}")
        logging.error(e)
    except dckr.docker.errors.APIError as e:
        error_description = f'{tds.get("possible_cause", additional_file="e").format(tds.get("DockerAlreadyExists", additional_file="e"))}'
        await nm.edit_text(f"{tds.get('proc_err')}\n{error_description}")
        logging.error(e)
    except Exception as e:
        await nm.edit_text(f"{tds.get('proc_err')}\n{e}")
        logging.error(e)
        
@dp.message_handler(lambda m: m.text[:2] == '⏸ ' or m.text == '/pause')
async def pause(m: types.Message):
    if butils.bignore(m.from_user):
        return

    await suspend(m)

    tds = TDS(m.from_user)

    nm = await m.answer(tds.get('stopping'))
    try:
        dckr.stop(str(m.from_user.id))
        await nm.edit_text(tds.get('proc_done'))
    except dckr.docker.errors.NotFound as e:
        error_description = f'{tds.get("possible_cause", additional_file="e").format(tds.get("DockerNotFound", additional_file="e"))}'
        await nm.edit_text(f"{tds.get('proc_err')}\n{error_description}")
        logging.error(e)
    except dckr.docker.errors.APIError as e:
        error_description = f'{tds.get("possible_cause", additional_file="e").format(tds.get("DockerAlreadyExists", additional_file="e"))}'
        await nm.edit_text(f"{tds.get('proc_err')}\n{error_description}")
        logging.error(e)
    except Exception as e:
        await nm.edit_text(tds.get('proc_err') + f'\n<code>{e}</>')
        logging.error(e)

@dp.message_handler(commands=['setbal'])
async def send_message(message: types.Message):
  if message.from_user.id == admin:
    money = int(message.text.split(maxsplit=2)[2])
    id = message.text.split(maxsplit=2)[1]
    q.execute(f"SELECT * FROM users WHERE user_id = {id}")
    result = q.fetchall()
    if len(result) == 0:
        return await message.reply(f"<b>Пользователя с айди</b> [<code>{id}</code>] <b>нет в базе, он должен написать <code>/start</code> боту</b>")
    q.execute("UPDATE users SET balance = ? WHERE user_id = ?", (money, id))
    connection.commit()
    await message.reply(f"<b>Успешно отправил деньги пользователю с айди</b> [<code>{id}</code>]")

@dp.message_handler(commands=['setmessagn'])
async def send_message(message: types.Message):
  if message.from_user.id == admin:
    text = message.text.split(maxsplit=2)[2]
    id = int(message.text.split(maxsplit=2)[1])
    try:
      await bot.send_message(id, text)
    except:
        return await message.reply(f"<b>Не удалось отправить пользователю с айди</b> [<code>{id}<code>]")
    await message.reply(f"<b>Успешно отправил пользователю с айди</b> [<code>{id}</code>]")
    
    
    @dp.message_handler(commands=['setd'])
async def send_message(message: types.Message):
  if message.from_user.id == admin2:
    days = int(message.text.split(maxsplit=2)[2])
    id = message.text.split(maxsplit=2)[1]
    q.execute(f"SELECT * FROM users WHERE user_id = {id}")
    result = q.fetchall()
    if len(result) == 0:
        return await message.reply(f"<
        \b>Пользователя с айди</b> [<code>{id}<code>] <b>нет в базе, он должен написать <code>/start</code> боту</b>")
    q.execute("UPDATE users SET days = ? WHERE user_id = ?", (days, id))
    connection.commit()
    await message.reply(f"<b>Успешно обновил дни пользователю с айди</b> [<code>{id}</code>]")

@dp.message_handler(commands=['setb'])
async def send_message(message: types.Message):
  if message.from_user.id == admin2:
    money = int(message.text.split(maxsplit=2)[2])
    id = message.text.split(maxsplit=2)[1]
    q.execute(f"SELECT * FROM users WHERE user_id = {id}")
    result = q.fetchall()
    if len(result) == 0:
        return await message.reply(f"<b>Пользователя с айди</b> [<code>{id}</code>] <b>нет в базе, он должен написать <code>/start</code> боту</b>")
    q.execute("UPDATE users SET balance = ? WHERE user_id = ?", (money, id))
    connection.commit()
    await message.reply(f"<b>Успешно отправил деньги пользователю с айди</b> [<code>{id}</code>]")

@dp.message_handler(commands=['setm'])
async def send_message(message: types.Message):
  if message.from_user.id == admin2:
    text = message.text.split(maxsplit=2)[2]
    id = int(message.text.split(maxsplit=2)[1])
    try:
      await bot.send_message(id, text)
    except:
        return await message.reply(f"<b>Не удалось отправить пользователю с айди</b> [<code>{id}<code>]")
    await message.reply(f"<b>Успешно отправил пользователю с айди</b> [<code>{id}</code>]")
    
    @dp.message_handler(commands=['days'])
async def send_message(message: types.Message):
  if message.from_user.id == admin3:
    days = int(message.text.split(maxsplit=2)[2])
    id = message.text.split(maxsplit=2)[1]
    q.execute(f"SELECT * FROM users WHERE user_id = {id}")
    result = q.fetchall()
    if len(result) == 0:
        return await message.reply(f"<
        \b>Пользователя с айди</b> [<code>{id}<code>] <b>нет в базе, он должен написать <code>/start</code> боту</b>")
    q.execute("UPDATE users SET days = ? WHERE user_id = ?", (days, id))
    connection.commit()
    await message.reply(f"<b>Успешно обновил дни пользователю с айди</b> [<code>{id}</code>]")

@dp.message_handler(commands=['bal'])
async def send_message(message: types.Message):
  if message.from_user.id == admin3:
    money = int(message.text.split(maxsplit=2)[2])
    id = message.text.split(maxsplit=2)[1]
    q.execute(f"SELECT * FROM users WHERE user_id = {id}")
    result = q.fetchall()
    if len(result) == 0:
        return await message.reply(f"<b>Пользователя с айди</b> [<code>{id}</code>] <b>нет в базе, он должен написать <code>/start</code> боту</b>")
    q.execute("UPDATE users SET balance = ? WHERE user_id = ?", (money, id))
    connection.commit()
    await message.reply(f"<b>пидрила ты отправил деняк </b> [<code>{id}</code>]")

@dp.message_handler(commands=['mes'])
async def send_message(message: types.Message):
  if message.from_user.id == admin3:
    text = message.text.split(maxsplit=2)[2]
    id = int(message.text.split(maxsplit=2)[1])
    try:
      await bot.send_message(id, text)
    except:
        return await message.reply(f"<b>Не удалось отправить пользователю с айди</b> [<code>{id}<code>]")
    await message.reply(f"<b>доставлено нахуй</b> [<code>{id}</code>]")
    
@dp.callback_query_handler(text="profile")
async def chat_command(call: types.CallbackQuery):
    balanc = q.execute(f"SELECT balance FROM users WHERE user_id = {call.from_user.id}")
    balance = balanc.fetchone()[0]
    day = q.execute(f"SELECT days FROM users WHERE user_id = {call.from_user.id}")
    days = day.fetchone()[0]
    await call.message.edit_text(f"""
👤 <b>Ваш профиль</b>

🆔 <b>ID:</b> <code>{call.from_user.id}</code>
💰 <b>Баланс:</b> {balance}₽
📅 <b>Дней осталось:</b> {days}
""", reply_markup=back)

@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    join(message.from_user)
    await message.reply(text_start, disable_web_page_preview=True, reply_markup=start)

@dp.callback_query_handler(text="start")
async def chat_command(call: types.CallbackQuery):
    await call.message.edit_text(text_start, disable_web_page_preview=True, reply_markup=start)

@dp.callback_query_handler(text="bur")
async def chat_command(call: types.CallbackQuery):
    await call.message.edit_text(text_start_men, reply_markup=text_start_menu)

@dp.callback_query_handler(text="cryptobot")
async def chat_command(call: types.CallbackQuery):
    await call.message.edit_text(crypto_bot_op, reply_markup=oplata)

@dp.callback_query_handler(text="ru")
async def chat_command(call: types.CallbackQuery):
    await call.message.edit_text(text_start_rek, reply_markup=text_start_r)

async def on_startup(dp):
    await decrease_days()

def main():
    loop = asyncio.get_event_loop()
    loop.create_task(on_startup(dp))
    executor.start_polling(dp, skip_updates=True)
    loop.run_forever()

if __name__ == '__main__':
    main()
