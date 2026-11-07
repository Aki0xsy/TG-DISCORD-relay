import asyncio
import logging
import os
from pathlib import Path

from aiohttp import web
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

import config
from discord_webhook import DiscordWebhook

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
log = logging.getLogger(__name__)

router = Router()
discord: DiscordWebhook | None = None


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("✅ Ретранслятор TG → Discord запущен.\nДобавь меня администратором в канал — сообщения начнут пересылаться в Discord.")


def message_link(message: Message) -> str | None:
    chat = message.chat
    if chat.username:
        return f"https://t.me/{chat.username}/{message.message_id}"
    chat_id = str(chat.id)
    if chat_id.startswith("-100"):
        return f"https://t.me/c/{chat_id[4:]}/{message.message_id}"
    return None


def get_media(message: Message):
    if message.photo:
        f = message.photo[-1]
        return f.file_id, "photo.jpg", f.file_size
    if message.animation:
        f = message.animation
        return f.file_id, f.file_name or "animation.mp4", f.file_size
    if message.video:
        f = message.video
        return f.file_id, f.file_name or "video.mp4", f.file_size
    if message.document:
        f = message.document
        return f.file_id, f.file_name or "document", f.file_size
    if message.voice:
        f = message.voice
        return f.file_id, "voice.ogg", f.file_size
    if message.audio:
        f = message.audio
        return f.file_id, f.file_name or "audio", f.file_size
    if message.video_note:
        f = message.video_note
        return f.file_id, "video_note.mp4", f.file_size
    return None


def build_text(message: Message) -> str:
    chat = message.chat
    source = chat.title or chat.username or str(chat.id)
    link = message_link(message)
    header = source + (f" · {link}" if link else "")
    text = message.text or message.caption or ""

    if message.reply_to_message:
        replied = (message.reply_to_message.text or message.reply_to_message.caption or "").strip()
        if replied:
            text = f"↩️ Ответ на: {replied[:120]}\n\n{text}"

    if not text:
        if message.poll:
            text = f"📊 Опрос: {message.poll.question}"
        elif message.location:
            text = f"📍 Локация: {message.location.latitude}, {message.location.longitude}"
        elif message.venue:
            text = f"📍 {message.venue.title}"
        elif message.contact:
            text = f"👤 Контакт: {message.contact.phone_number}"
        elif get_media(message):
            text = "📎 Медиа без подписи"
        else:
            text = ""

    return f"**{header}**\n{text}".strip() if text else f"**{header}**"


@router.channel_post()
async def handle_channel_post(message: Message, bot: Bot):
    global discord
    if discord is None:
        return
    if config.SOURCE_CHANNEL_IDS and message.chat.id not in config.SOURCE_CHANNEL_IDS:
        return

    text = build_text(message)
    media = get_media(message)
    if not text and not media:
        return

    log.info("Forward %s from chat %s", message.message_id, message.chat.id)
    username = message.chat.title or message.chat.username or "Telegram"
    try:
        if media:
            file_id, filename, file_size = media
            max_bytes = config.MAX_FILE_MB * 1024 * 1024
            if file_size and file_size > max_bytes:
                await discord.send_text(f"{text}\n\n📎 Файл пропущен: больше {config.MAX_FILE_MB} MB (лимит Discord).", username=username)
                return
            # Telegram file_id is not a file_path. Resolve it first, then download
            # using the path returned by get_file (required by aiogram 3.x).
            telegram_file = await bot.get_file(file_id)
            if not telegram_file.file_path:
                raise RuntimeError(f"Telegram did not return file_path for {filename}")
            downloaded = await bot.download_file(telegram_file.file_path)
            downloaded.seek(0)
            await discord.send_file(downloaded.read(), filename, text, username=username)
        else:
            await discord.send_text(text, username=username)
    except Exception:
        log.exception("Failed to forward message %s", message.message_id)


async def health(request: web.Request) -> web.Response:
    return web.json_response({"ok": True, "relay": "tg->discord"})


async def main():
    if not config.TELEGRAM_BOT_TOKEN:
        raise SystemExit("❌ Не задан TELEGRAM_BOT_TOKEN")
    if not config.DISCORD_WEBHOOK_URL:
        raise SystemExit("❌ Не задан DISCORD_WEBHOOK_URL")

    global discord
    discord = DiscordWebhook(config.DISCORD_WEBHOOK_URL)

    bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    runner = None
    if config.PORT:
        app = web.Application()
        app.router.add_get("/health", health)
        app.router.add_get("/", health)
        runner = web.AppRunner(app)
        await runner.setup()
        await web.TCPSite(runner, "0.0.0.0", config.PORT).start()
        log.info("Health server on port %s", config.PORT)

    await bot.delete_webhook(drop_pending_updates=config.DROP_PENDING_UPDATES)
    log.info("Relay bot started")
    try:
        await dp.start_polling(bot)
    finally:
        if runner:
            await runner.cleanup()
        await discord.close()


if __name__ == "__main__":
    asyncio.run(main())
