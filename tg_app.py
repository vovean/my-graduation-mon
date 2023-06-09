import asyncio
import logging
import math
import pathlib
import pickle

import telegram.ext
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

import config
import servers


def get_registered_users() -> set[int]:
    try:
        with open(pathlib.Path(__file__).parent / 'data' / 'allowed_users.pickle', 'rb') as fin:
            data = pickle.load(fin)
            return data
    except FileNotFoundError:
        logging.info('file with known users not found')
    except Exception as e:
        logging.warning('failed to get registered users', exc_info=e)

    return set()


def save_registered_users(users: set[int]):
    with open(pathlib.Path(__file__).parent / 'data' / 'allowed_users.pickle', 'wb') as fout:
        pickle.dump(users, fout)


class TGAppController:
    def __init__(self, secret_key: str, cfg: config.Config, sm: servers.Manager):
        self.users = get_registered_users()
        self.secret_key = secret_key
        self.application = ApplicationBuilder().token(cfg.bot_token).build()
        self.sm = sm

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Данный бот отвечает за мониторинг состояние серверов, к которым предоставляется доступ через телеграм-бота\n'
                 '*Команды:*\n'
                 '1. /start - вывести данное сообщение\n'
                 '2. /register - зарегистрироваться в боте, требуется предоставить секретный ключ\n'
                 '3. /servers - вывести список известных серверов и их статусы\n'
                 '\n'
                 f'Статус пользователя: {"Авторизован" if update.effective_user.id in self.users else "Не авторизован. Для авторизации используйте команду /register"}\n'
                 '\n'
                 '_Секретный ключ создается один раз - при первом запуске мониторинг-бота. Его нужно сохранить в надежное место для дальнейшего использования._\n'
                 '_После успешной регистрации рекомендуется удалить сообщение с секретным ключом в целях безопасности._',
            parse_mode='Markdown'
        )

    async def notify_users_on_new_server(self, server: str):
        for user in self.users:
            await self.application.bot.send_message(
                chat_id=user,
                text=f'Зарегистрирован новый сервер: `{server}`',
                parse_mode='Markdown',
            )

    async def notify_users_server_active_again(self, server: str):
        for user in self.users:
            await self.application.bot.send_message(
                chat_id=user,
                text=f'Сервер снова активен: `{server}`',
                parse_mode='Markdown',
            )

    async def register(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text
        tokens = text.split(' ', maxsplit=1)
        if len(tokens) != 2:
            await update.effective_message.reply_text(
                text='Недопустимый формат сообщения. Правильный формат: `/register your-secret-key`',
                parse_mode='Markdown',
            )
            return

        sk = tokens[1]
        if sk != self.secret_key:
            await update.effective_message.reply_text(
                text='Неверный секретный ключ. Попробуйте еще раз или обратитесь к администратору'
            )
            return

        self.users.add(update.effective_user.id)
        save_registered_users(self.users)

        await update.effective_message.reply_text(
            text='Доступ предоставлен. Вы можете увидеть список серверов и их статус с помощью команды /servers'
        )

    async def get_servers(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in self.users:
            await update.effective_message.reply_text(
                text="Нет доступа к просмотру серверов. Чтобы получить доступ нужно использовать команду /register",
                parse_mode='Markdown',
            )
            return

        known_servers = self.sm.get_servers()

        if len(known_servers) == 0:
            await update.effective_message.reply_text(
                text='Нет зарегистрированных серверов'
            )
            return

        text = ''
        max_index_len = math.ceil(math.log10(len(known_servers)))

        for i, server_info in enumerate(known_servers.items()):
            server, is_active = server_info
            text += f'{i + 1:{max_index_len}d}. `{server:15s}` {"🟢" if is_active else "🔴"}\n'

        await update.effective_message.reply_text(
            text=text,
            parse_mode='Markdown',
        )

    async def notify_on_server_getting_inactive(self, _: telegram.ext.CallbackContext):
        inactive_to_notify = self.sm.get_inactive_not_notified()
        for server in inactive_to_notify:
            for user in self.users:
                await self.application.bot.send_message(
                    chat_id=user,
                    text=f'Сервер стал неактивным: `{server}`',
                    parse_mode='Markdown',
                )
                await asyncio.sleep(0.05)
        self.sm.set_inactive_notified(inactive_to_notify)

    def get_tg_app(self) -> telegram.ext.Application:
        self.application.job_queue.run_repeating(self.notify_on_server_getting_inactive, interval=1)
        self.application.add_handlers([
            CommandHandler('start', self.start),
            CommandHandler('register', self.register),
            CommandHandler('servers', self.get_servers),
        ])
        return self.application
