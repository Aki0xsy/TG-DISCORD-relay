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

## Render Keep-Alive (GitHub Actions)

В архив добавлен workflow `.github/workflows/render-keepalive.yml`. После загрузки проекта в GitHub в **основную ветку** он будет обращаться к `https://tg-discord-relay.onrender.com/health` каждые 5 минут. Если Render ещё запускает уснувший сервис, workflow повторит запрос до 5 раз.

Чтобы включить:
1. Загрузите содержимое проекта в GitHub-репозиторий (именно в default branch).
2. Откройте вкладку **Actions** и разрешите запуск workflows, если GitHub попросит.
3. Откройте workflow **Keep Render Relay Awake** и нажмите **Run workflow** для первой проверки.
4. В разделе **Actions** проверьте, что запуск завершился зелёной галочкой.

GitHub Actions cron может запускаться с задержкой и не является гарантированным таймером. Render также может перезапускать Free-сервис по своим причинам; keep-alive предотвращает только простой из-за отсутствия входящего трафика, но не заменяет постоянно работающий платный экземпляр.
