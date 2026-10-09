# Уведомления от Claude в Telegram

`scripts/notify_telegram.py` отправляет сообщения через Telegram Bot API (только стандартная библиотека Python).
`.claude/settings.json` подключает его как hook Claude Code:

- **Stop**: Claude закончил ответ, в сообщение попадает его последний текст;
- **Notification**: Claude ждёт вашего ответа или разрешения.

## Настройка

1. Создайте бота через [@BotFather](https://t.me/BotFather) и получите токен.
2. Напишите боту любое сообщение, затем откройте
   `https://api.telegram.org/bot<TOKEN>/getUpdates` и возьмите `message.chat.id`.
3. Задайте переменные окружения (в облачном окружении Claude Code: настройки окружения → Edit):
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`: один id или несколько через запятую, например `111111111,-1002222222222`
     (сообщение уйдёт в каждый чат)

Не коммитьте токен в репозиторий.

## Ручная отправка

```sh
python3 scripts/notify_telegram.py "Привет из Claude"
echo "текст из stdin" | python3 scripts/notify_telegram.py
```

## Периодические задачи

Используйте Routine (запуск по расписанию) в Claude Code: на каждый запуск создаётся
новая сессия на этом репозитории, Claude выполняет задачу, а hook `Stop` присылает результат в Telegram.
