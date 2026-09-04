# Beauty Master Bot + Website

Демо-проект для бьюти-сферы: Telegram-бот записи + сайт-визитка.

## Возможности

- минимальный Telegram-бот;
- одна кнопка для открытия Mini App;
- услуги и цены в Mini App;
- выбор нескольких услуг в Mini App;
- запись через свободные окна по графику, дате и времени;
- админ-панель в Mini App;
- добавление и удаление свободных окон;
- просмотр заявок;
- подтверждение или отмена заявки из Mini App или сообщения админу;
- SQLite;
- статичный сайт в `site/`.

## Запуск бота

Создайте `.env`:

```env
BOT_TOKEN=your_token_here
ADMIN_ID=123456789
DB_PATH=beauty_bot.db
MINI_APP_URL=https://your-domain.up.railway.app/miniapp
PORT=8000
```

Локально база хранится в файле `beauty_bot.db` рядом с кодом проекта.
Даже если указать `DB_PATH=beauty_bot.db`, путь будет привязан к папке проекта.
Так расписание не будет зависеть от того, из какой папки запустили Python.

Для Railway подключите Volume и задайте:

```env
DB_PATH=/data/beauty_bot.db
```

Без Volume SQLite-файл может пропасть после перезапуска или redeploy.

Запуск:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Если `MINI_APP_URL` задан, кнопка в боте открывает Mini App. Если URL не задан, бот покажет обычную кнопку без открытия Web App.

## Админ-панель

```text
/admin
```

Админ управляет окнами и заявками в Mini App.

Добавление окон сделано коротким сценарием:

1. `/admin`
2. `➕ Додати вікна`
3. выбрать график;
4. выбрать дату кнопкой или ввести вручную;
5. ввести время списком: `10:00, 12:00, 15:30`.

Статусы слотов:

- `free` — время свободно;
- `blocked` — клиент отправил заявку, мастер ещё не решил;
- `booked` — мастер подтвердил запись.

Если мастер отменяет заявку, слот снова становится свободным.

## Сайт

Локально после запуска бота:

```text
http://localhost:8000/
```

На Railway:

```text
https://your-domain.up.railway.app/
```

Менять данные:

```text
site/data.js
```

Там лежат название, город, услуги, цены, мастера, портфолио, контакты, Telegram, Instagram и цвет.

## Mini App

Файлы Mini App лежат в:

```text
miniapp/
```

Адрес локально:

```text
http://localhost:8000/miniapp
```

Для Telegram нужен публичный HTTPS-адрес, например Railway:

```text
https://your-domain.up.railway.app/miniapp
```

Этот адрес нужно указать в `MINI_APP_URL`.

Схема адресов на сервере:

```text
/        сайт-визитка
/miniapp Telegram Mini App для записи
```

## Основные файлы

- `main.py` — запуск бота;
- `handlers.py` — минимальный бот и служебные действия админа;
- `database.py` — SQLite;
- `keyboards.py` — кнопка Mini App и кнопки подтверждения заявки;
- `data.py` — данные бота;
- `webapp.py` — API, сайт и сервер Mini App;
- `miniapp/` — интерфейс записи внутри Telegram;
- `site/` — сайт-визитка.

## Важно

Проект демонстрационный. Фото, отзывы, контакты, цены и ссылки нужно заменить под реального клиента.
