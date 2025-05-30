# proudly vibecoded and edited by awenkoo

import os
import time
from dotenv import load_dotenv
import telebot

BOT_TIMEOUT_SECONDS = 30

RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RESET = "\033[0m"


HEADER = "Шановні користувачі!\n\n"
FOOTER = "\n\nКоманда KSU24"

templates = {
    "ok": {
        "custom": {
            "template": "✅ {text}",
            "needs_text": True,
        },
        "maintenance": {
            "template": "✅ Планове технічне обслуговування закінчено.\nСервіс працює у штатному режимі.",
            "needs_text": False,
        },
    },
    "warn": {
        "custom": {
            "template": "⚠️ {text}",
            "needs_text": True,
        },
        "maintenance": {
            "template": "⚠️ Незабаром буде планове технічне обслуговування.\nБудь ласка, не ",
            "needs_text": False,
        },
    },
}

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

# bruh
ALLOWED_USERS = (
    set(map(int, os.getenv("ALLOWED_USERS", "").split(",")))
    if os.getenv("ALLOWED_USERS")
    else set()
)

bot = telebot.TeleBot(BOT_TOKEN)
states = {}


def kb_buttons(items, prefix):
    kb = telebot.types.InlineKeyboardMarkup()
    for i in items:
        kb.add(
            telebot.types.InlineKeyboardButton(
                i.capitalize(), callback_data=f"{prefix}{i}"
            )
        )
    return kb


def send_btn():
    kb = telebot.types.InlineKeyboardMarkup()
    kb.add(
        telebot.types.InlineKeyboardButton(
            "📤 Надіслати до каналу", callback_data="send"
        )
    )
    return kb


def get_tpl(uid):
    s = states.get(uid, {})
    if s.get("category") and s.get("template"):
        return templates[s["category"]][s["template"]]


def make_message(uid):
    tpl = get_tpl(uid)
    if not tpl:
        return None
    body = (
        tpl["template"].format(text=states[uid].get("text", ""))
        if tpl["needs_text"]
        else tpl["template"]
    )
    return HEADER + body + FOOTER


@bot.message_handler(commands=["start"])
def start(m):
    if m.from_user.id not in ALLOWED_USERS:
        return
    bot.send_message(
        m.chat.id,
        "Оберіть категорію повідомлення:",
        reply_markup=kb_buttons(templates.keys(), "cat_"),
    )


@bot.callback_query_handler(func=lambda c: c.from_user.id in ALLOWED_USERS)
def cb(c):
    uid, data = c.from_user.id, c.data

    if data.startswith("cat_"):
        cat = data[4:]
        states[uid] = {"category": cat}
        bot.edit_message_text(
            f"Категорія: {cat.capitalize()}\nОберіть шаблон:",
            c.message.chat.id,
            c.message.message_id,
            reply_markup=kb_buttons(templates[cat].keys(), "sub_"),
        )

    elif data.startswith("sub_"):
        sub = data[4:]
        cat = states[uid]["category"]
        states[uid]["template"] = sub
        tpl = templates[cat][sub]
        if tpl["needs_text"]:
            bot.edit_message_text(
                "Введіть текст повідомлення:", c.message.chat.id, c.message.message_id
            )
        else:
            bot.edit_message_text(
                make_message(uid),
                c.message.chat.id,
                c.message.message_id,
                reply_markup=send_btn(),
            )

    elif data == "send":
        msg = make_message(uid)
        if not msg:
            bot.edit_message_text(
                "Немає даних для відправлення.",
                c.message.chat.id,
                c.message.message_id,
            )
            return

        sent_msg = bot.send_message(CHANNEL_ID, msg)
        channel_link = f"https://t.me/c/{str(CHANNEL_ID)[4:]}/{sent_msg.message_id}"

        bot.edit_message_text(
            f"✅ [Повідомлення надіслано!]({channel_link})",
            c.message.chat.id,
            c.message.message_id,
            parse_mode="Markdown",
        )
        states.pop(uid, None)


@bot.message_handler(
    func=lambda m: m.from_user.id in ALLOWED_USERS
    and m.from_user.id in states
    and "template" in states[m.from_user.id]
)
def txt(m):
    uid = m.from_user.id
    states[uid]["text"] = m.text
    preview = make_message(uid)
    bot.send_message(m.chat.id, preview, reply_markup=send_btn())


if __name__ == "__main__":
    try:
        while True:
            try:
                print(f"{GREEN}Info: Бота запущено!{RESET}")
                bot.polling(interval=1)
            except Exception as e:
                print(f"{RED}{e}{RESET}")
                print(
                    f"{YELLOW}Warn: Перезапуск бота через {BOT_TIMEOUT_SECONDS} секунд{RESET}"
                )
                time.sleep(BOT_TIMEOUT_SECONDS)
    except KeyboardInterrupt:
        # інколи бажано поспамить Ctrl+C
        print(f"\n{YELLOW}Warn: Бота зупинено (Ctrl+C){RESET}")
