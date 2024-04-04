import os
import re
import logging
import sqlite3
import threading
from io import BytesIO
from decouple import config
import qrcode
import telebot
from telebot import types

# Set up logging
logging.basicConfig(filename="app.log", level=logging.INFO)

# Create a lock for SQLite operations
sqlite_lock = threading.Lock()

# Create or connect to a SQLite database
conn = sqlite3.connect("bot.db", check_same_thread=False)
c = conn.cursor()

# Create a table to store user history
c.execute(
    """CREATE TABLE IF NOT EXISTS user_history
             (user_id INTEGER, input TEXT, timestamp DATETIME)"""
)


class QRCodeGenerator:
    def __init__(
        self,
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    ):
        self.version = version
        self.error_correction = error_correction
        self.box_size = box_size
        self.border = border

    def create(self, data):
        try:
            qr = qrcode.QRCode(
                version=self.version,
                error_correction=self.error_correction,
                box_size=self.box_size,
                border=self.border,
            )
            qr.add_data(data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")

            # Create a BytesIO object to store the PNG image
            img_bytes = BytesIO()
            img.save(img_bytes, "PNG")
            img_bytes.seek(
                0
            )  # Reset the pointer to the beginning of the BytesIO object
            return img_bytes
        except Exception as e:
            logging.error(f"Error generating QR code: {e}")
            return None


def is_valid_url(url):
    url_regex = r"^(http|https)://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/\S*)?$"
    return bool(re.match(url_regex, url))


def store_history(user_id, user_name, input_text):
    def store_history_thread():
        with sqlite_lock:
            try:
                c.execute(
                    "INSERT INTO user_history (user_id, user_name, input, timestamp) VALUES (?, ?, CURRENT_TIMESTAMP)",
                    (user_id, input_text),
                )
                conn.commit()
            except sqlite3.Error as e:
                logging.error(f"Error storing user history: {e}")

    thread = threading.Thread(target=store_history_thread)
    thread.start()


class Bot:
    def __init__(self):
        self.bot = telebot.TeleBot(os.environ["TOKEN"])
        self.setup_handler()

    def setup_handler(self):
        @self.bot.message_handler(commands=["start"])
        def send_welcome(message):
            menu_keyboard = types.ReplyKeyboardMarkup(row_width=2)
            menu_options: list[str] = ["/QR_Code", "/help"]
            menu_buttons = [
                types.KeyboardButton(text=option) for option in menu_options
            ]
            menu_keyboard.add(*menu_buttons)

            self.bot.reply_to(
                message, "Welcome to the QR code generator", reply_markup=menu_keyboard
            )

        @self.bot.message_handler(commands=["QR_Code"])
        def _qr(message):
            self.bot.reply_to(message, "Send your link or text")
            self.bot.register_next_step_handler(message, convert)

        def convert(message):
            _input = message.text
            user_id = message.from_user.id
            chat_id = message.chat.id
            if is_valid_url(_input):
                qr_code = QRCodeGenerator().create(_input)
                if qr_code:
                    try:
                        self.bot.send_photo(message.chat.id, qr_code)
                        store_history(user_id, chat_id, _input)
                    except telebot.apihelpers.ApiException as e:
                        logging.error(f"Error sending QR code photo: {e}")
                        self.bot.reply_to(
                            message,
                            "An error occurred while sending the QR code photo.",
                        )
                else:
                    self.bot.reply_to(
                        message, "An error occurred while generating the QR code."
                    )
            else:
                self.bot.reply_to(message, "Invalid URL. Please enter a valid URL.")

    def start_pooling(self):
        self.bot.polling()


if __name__ == "__main__":
    os.environ["TOKEN"] = config("BOT_TOKEN")
    bot = Bot()
    bot.start_pooling()
