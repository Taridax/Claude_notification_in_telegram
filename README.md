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
     Без `--chat` сообщения (в том числе уведомления hook) уходят только в личные чаты;
     в группы (id с минусом) отправляется только то, что адресовано им явно через `--chat`.

Не коммитьте токен в репозиторий.

## Ручная отправка

```sh
python3 scripts/notify_telegram.py "Привет из Claude"
echo "текст из stdin" | python3 scripts/notify_telegram.py
```

## Ежедневный дайджест законодательства

`scripts/fetch_feeds.py` читает RSS lex.uz и norma.uz и выдаёт записи, которых нет в
`state/seen.json`. По будням в 9:12 (Ташкент) Routine запускает Claude по инструкции
[`DIGEST.md`](DIGEST.md): Claude отбирает новости о строительстве и проектировании и
отправляет дайджест в группу. Если подходящих новостей нет, ничего не отправляется.
Чтобы изменить тематику или формат, отредактируйте `DIGEST.md`.

```sh
python3 scripts/fetch_feeds.py          # новые записи (JSON), состояние не меняется
python3 scripts/fetch_feeds.py --all    # все записи из лент
python3 scripts/notify_telegram.py --chat -1003022426387 "текст"   # отправка в один чат
```
