# TG → Discord Webhook Relay

Пересылает публикации из Telegram-каналов в один Discord-канал через Discord Webhook.

## Настройка

Переменные окружения (или локальный `.env`):

- `TELEGRAM_BOT_TOKEN` — токен отдельного бота от @BotFather.
- `DISCORD_WEBHOOK_URL` — URL Discord Webhook.
- `SOURCE_CHANNEL_IDS` — необязательно, ID каналов через запятую. Пустое значение означает все каналы, где бот администратор.
- `MAX_FILE_MB` — максимальный размер вложения, по умолчанию 24.
- `PORT` — порт health endpoint, для Railway обычно 8000.
- `DROP_PENDING_UPDATES` — `1` чтобы пропускать очередь старых обновлений при запуске.

## Запуск

```bash
pip install -r requirements.txt
python bot.py
```

Проверка состояния: `GET /health` (если задан `PORT`).

## Важно

1. Добавьте бота **администратором** в каждый исходный Telegram-канал. Для пересылки публикаций используется `channel_post`.
2. Запускайте только **один экземпляр** бота с данным токеном. Два polling-процесса с одним токеном конфликтуют (`TelegramConflictError: terminated by other getUpdates request`).
3. На Railway задайте `TELEGRAM_BOT_TOKEN`, `DISCORD_WEBHOOK_URL`, `PORT=8000`.
4. Не публикуйте `.env` и не добавляйте его в репозиторий. Используйте `.env.example` как шаблон.
5. Это направление только Telegram → Discord. Webhook не читает сообщения Discord.

Поддерживаются текст, фото, документы, видео, аудио, голосовые и video notes. Слишком большие вложения пропускаются с уведомлением.
