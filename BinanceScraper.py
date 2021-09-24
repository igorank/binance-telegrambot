import time
import logging
import sqlite3
import requests

from aiogram import Bot, Dispatcher, executor, types

TOKEN = ' ' # необходимо заполнить
CRYPTS_PAIR = ["ETHUSDT", "BTCUSDT", "LTCUSDT", "XRPUSDT", "BNBUSDT", "DOGEUSDT"]

is_running = False
current_total = 0.0
current_price = 0.0
previous_total = 0.0
previous_price = 0.0

class SQLighter :

    def __init__(self, database_file):
        self.connection = sqlite3.connect(database_file)
        self.cursor = self.connection.cursor()

    def get_subcriptions(self, status = True):
        with self.connection:
            return self.cursor.execute("SELECT * FROM `subscriptions` WHERE `status` = ?",
                                       (status,)).fetchall()

    def subscriber_exists(self, user_id):
        with self.connection:
            result = self.cursor.execute("SELECT * FROM `subcriptions` WHERE `user_id`= ?",
                                         (user_id,)).fetchall()
            return bool(len(result))

    def add_subscriber(self, user_id, status = True):
        with self.connection:
            return self.cursor.execute("INSERT INTO `subcriptions` (`user_id`, `status`) VALUES (?,?)",
                                       (user_id, status))

    def update_subscription(self, user_id, status):
        return self.cursor.execute("UPDATE `subcriptions` SET `status` = ? WHERE `user_id` = ?",
                                   (status, user_id))

    def close(self):
        self.connection.close()

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

db = SQLighter('db.db')

@dp.message_handler(commands=['subscribe'])
async def subscribe(message: types.Message):
    if not db.subscriber_exists(message.from_user.id):
        db.add_subscriber(message.from_user.id)
    else:
        db.update_subscription(message.from_user.id, True)
    await message.answer("Вы успешно подписались!")

@dp.message_handler(commands=['unsubscribe'])
async def unsubscribe(message: types.Message):
    if not db.subscriber_exists(message.from_user.id):
        db.add_subscriber(message.from_user.id, False)
        await message.answer("Вы и так не подписаны.")
    else:
        db.update_subscription(message.from_user.id, False)
        await message.answer("Вы успешно отписаны.")

@dp.message_handler(commands=['start'])
async def message(message: types.Message):
    global is_running
    is_running = True
    global current_total
    global previous_total
    global current_price
    global previous_price
    await bot.send_message(message.from_user.id, "Парсер запущен!")
    while is_running is True:
        for p in CRYPTS_PAIR:
            r = requests.get("https://api.binance.com/api/v3/depth", params=dict(symbol=p))
            results = r.json()
            r2 = requests.get("https://api.binance.com/api/v3/ticker/24hr", params=dict(symbol=p))
            results2 = r2.json()

            for x in range(0,100):
                if ((float(results["bids"][x][0]) * float(results["bids"][x][1])) > (float(results2["quoteVolume"]) / 250.0) and
                    (((float(results["bids"][x][0]) * float(results["bids"][x][1])) != current_total) and
                    (float(results["bids"][x][0]) != current_price)) and
                    (((float(results["bids"][x][0]) * float(results["bids"][x][1])) != previous_total) and
                    (float(results["bids"][x][0]) != previous_price))):
                    previous_total = current_total
                    previous_price = current_price
                    current_total = float(results["bids"][x][0]) * float(results["bids"][x][1])
                    current_price = float(results["bids"][x][0])
                    if len(p) == 7:
                        await bot.send_message(message.from_user.id, str(p[0:3]) + '/' + str(p[3:]) + ":\nPrice - " + results["bids"][x][0]
                                               + "\nTotal (USDT) - " + str(float(results["bids"][x][0]) * float(results["bids"][x][1])))
                    else:
                        await bot.send_message(message.from_user.id, str(p[0:4]) + '/' + str(p[4:]) + ":\nPrice - " + results["bids"][x][0]
                                               + "\nTotal (USDT) - " + str(float(results["bids"][x][0]) * float(results["bids"][x][1])))
    time.sleep(1)


@dp.message_handler(commands=['stop'])
async def message(message: types.Message):
    await bot.send_message(message.from_user.id, "Парсер остановлен!")
    global is_running
    is_running = False

if __name__== '__main__':
    executor.start_polling(dp, skip_updates=True)
