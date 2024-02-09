from nakuru.entities.components import *
from nakuru import (
    GroupMessage,
    FriendMessage
)
from botpy.message import Message, DirectMessage
try:
    from util.plugin_dev.api.v1.config import *
    from util.plugin_dev.api.v1.message import AstrMessageEvent, MessageResult, message_handler, CommandResult
    from util.plugin_dev.api.v1.bot import GlobalObject
except ImportError:
    raise Exception("astrbot_plugin_telegram: 依赖导入失败。原因：请升级 AstrBot 到最新版本。")
from model.platform._nakuru_translation_layer import NakuruGuildMessage
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import asyncio
import threading

class Main:
    def __init__(self) -> None:
        self.loop = asyncio.new_event_loop()
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.ERROR
        )
        self.NAMESPACE = "tx_astrbot_plugin_telegram"
        put_config(self.NAMESPACE, "是否启用 Telegram 平台", "telegram_enable", False, "是否启用 Telegram 平台")
        put_config(self.NAMESPACE, "telegram_token", "telegram_token", "", "Telegram Bot 的 Token")
        put_config(self.NAMESPACE, "telegram_api_url", "telegram_api_url", "https://api.telegram.org/bot", "Telegram API 地址")
        put_config(self.NAMESPACE, "start_message", "start_message", "I'm AstrBot, please talk to me!", "Telegram 的 /start 开始消息")
        put_config(self.NAMESPACE, "allowed_user_id", "allowed_user_id", 6161175974, "允许使用指令的 Telegram 用户ID")
        self.cfg = load_config(self.NAMESPACE)
        self.start_message = self.cfg["start_message"]
        if self.cfg["telegram_enable"] and self.cfg["telegram_token"]:
            self.thread = threading.Thread(target=self.run_telegram_bot, args=(self.loop,)).start()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(chat_id=update.effective_chat.id, text=self.start_message)

    async def message_handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # 验证
        allowed_user_id = self.cfg.get('allowed_user_id', 6161175974)
        if update.effective_chat.id != allowed_user_id:
            return  # 1

        # 检查
        if update.message.chat.type == "group" or update.message.chat.type == "supergroup":
            # 获取
            bot_username = context.bot.username.lower()

            # 6
            if f"@{bot_username}" not in update.message.text.lower():
                return  

        message = NakuruGuildMessage()
        message.user_id = update.effective_chat.id
        message.message = [Plain(update.message.text),]
        result = await message_handler(
            message=message,
            platform="telegram",
            session_id=update.effective_chat.id,
            role="member",
        )
        plain_text = ""
        image_path = None
        if isinstance(result.result_message, str):
            await context.bot.send_message(chat_id=update.effective_chat.id, text=result.result_message)
            return
        for i in result.result_message:
            if isinstance(i, Plain):
                plain_text += i.text
            elif isinstance(i, Image):
                if i.path is not None:
                    image_path = i.path
                else:
                    image_path = i.file
                await context.bot.send_photo(chat_id=update.effective_chat.id, photo=image_path)
        if plain_text != "":
            await context.bot.send_message(chat_id=update.effective_chat.id, text=plain_text)

    def run_telegram_bot(self, loop: asyncio.AbstractEventLoop = None):
        asyncio.set_event_loop(loop)
        telegram_api_url = self.cfg.get('telegram_api_url', 'https://api.telegram.org/bot')
        self.application = ApplicationBuilder().token(self.cfg['telegram_token']).api_url(telegram_api_url).build()
        start_handler = CommandHandler('start', self.start)
        message_handler = MessageHandler(filters.TEXT, self.message_handle)
        self.application.add_handler(start_handler)
        self.application.add_handler(message_handler)
        self.application.run_polling(stop_signals=None)

    def run(self, ame: AstrMessageEvent):
        return CommandResult(
            hit=False,
            success=False,
            message_chain=[]
        )

    def info(self):
        return {
            "plugin_type": "platform",
            "name": "Tx-astrbot_plugin_telegram",
            "desc": "接入 Telegram 的插件",
            "help": "帮助信息查看：https://github.com/xinghanxu666/Tx-astrbot_plugin_telegram",
            "version": "v1.1.8",
            "author": "xinghanxu",
            "repo": "https://github.com/xinghanxu666/Tx-astrbot_plugin_telegram"
        }
