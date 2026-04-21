# 💅 Lash Studio API - Студия красоты (Наращивание ресниц и ламинирование бровей)

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18.3-4169E1?logo=postgresql)](https://www.postgresql.org)
[![Railway](https://img.shields.io/badge/Railway-Deployed-0B0D0E?logo=railway)](https://railway.app)

Современное веб-приложение для студии красоты Lash Studio. Клиенты могут записываться на услуги с выбором объёма ресниц (1D, 1.5D, 2D, 3D), а администратор управляет ценами, записями, контентом и галереей через удобную админ-панель.

---

## 🚀 Функционал

### Для клиентов
- ✅ Запись на услуги (ресницы, брови, комплекс)
- ✅ Выбор объёма ресниц (1D, 1.5D, 2D, 3D)
- ✅ Просмотр цен и портфолио
- ✅ Оставление отзывов с рейтингом и эмодзи
- ✅ Добавление сайта на экран «Домой» (PWA-like)
- ✅ Адаптивный дизайн для мобильных устройств

### Для администратора
- ✅ Управление ценами (все услуги + объёмы ресниц)
- ✅ Просмотр и управление записями (подтверждение, отмена, удаление)
- ✅ Календарь с визуализацией записей
- ✅ Управление галереей (загрузка/удаление фото)
- ✅ Редактирование контента главной страницы
- ✅ Модерация отзывов
- ✅ Финансовая статистика (выручка по услугам и объёмам)
- ✅ Управление часами работы и выходными днями
- ✅ Адаптивная админ-панель для мобильных

---

## 🛠 Технологии

### Бэкенд
- **FastAPI** — асинхронный веб-фреймворк
- **SQLAlchemy** — ORM для работы с БД
- **asyncpg** — асинхронный драйвер PostgreSQL
- **Pydantic** — валидация данных

### База данных
- **PostgreSQL** — основная БД (Railway)
- **SQLite** — для локальной разработки

### Фронтенд
- **HTML5 / CSS3** — адаптивная вёрстка
- **Vanilla JavaScript** — без фреймворков
- **Fetch API** — взаимодействие с бэкендом

### Деплой
- **Railway** — хостинг и деплой
- **GitHub Actions** — CI/CD

---

## 📦 Установка и запуск (локально)

### 1. Клонирование репозитория
```bash
git clone https://github.com/Sergey-Molchan/lash_api.git
cd lash_apihttp://localhost:8000/api/admin/bookings"

python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

pip install -r requirements.txt

Создай файл .env в корне проекта:

env
DATABASE_URL=sqlite+aiosqlite:///./lashes.db
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

lash_api/
├── app/
│   ├── routers/           # API роутеры
│   │   ├── admin.py       # Админ-панель
│   │   ├── client.py      # Клиентские запросы
│   │   ├── calendar.py    # Календарь
│   │   ├── prices.py      # Управление ценами
│   │   ├── gallery.py     # Галерея (фото в БД)
│   │   ├── comments.py    # Отзывы
│   │   ├── finance.py     # Финансовая статистика
│   │   └── ...
│   ├── templates/         # HTML шаблоны
│   │   ├── client/        # Клиентские страницы
│   │   │   ├── index.html
│   │   │   ├── booking.html
│   │   │   ├── portfolio.html
│   │   │   └── thankyou.html
│   │   └── admin/         # Админ-панель
│   ├── static/            # Статические файлы
│   │   ├── images/        # Фото для главной страницы
│   │   └── uploads/       # Загруженные фото (Volume)
│   ├── models.py          # SQLAlchemy модели
│   ├── database.py        # Подключение к БД
│   └── main.py            # Точка входа
├── requirements.txt       # Зависимости
└── README.md              # Документация


🔗 API Эндпоинты (основные)

Метод	URL	Описание
GET	/api/prices	Получить цены
POST	/api/prices/	Обновить цену
POST	/api/client/book	Создать запись
GET	/api/client/available-slots	Свободные слоты
GET	/api/admin/bookings	Список записей
POST	/api/admin/confirm/{id}	Подтвердить запись
GET	/api/gallery	Список фото галереи
POST	/api/gallery/upload	Загрузить фото
GET	/api/comments/approved	Одобренные отзывы
GET	/api/finance/month/{year}/{month}	Финансовая статистика


URL	Описание
/	Главная страница
/booking	Запись на услуги
/portfolio	Портфолио работ
/api/admin	Админ-панель
/thankyou	Страница благодарности
/add-to-home	Инструкция для добавления на экран «Домой»


🔐 Доступ в админ-панель

URL: /api/admin
Логин: ADMIN_USERNAME (переменная окружения)
Пароль: ADMIN_PASSWORD (переменная окружения)
🗄️ База данных (основные таблицы)

Таблица	Описание
bookings	Записи клиентов
prices	Цены на услуги
gallery_images	Фото для портфолио (хранятся в БД)
home_images	Фото для главной страницы
comments	Отзывы клиентов
working_hours	Выходные дни
day_hours	Часы работы
site_content	Контент главной страницы


📦 Зависимости

Основные пакеты (см. requirements.txt):

fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
asyncpg==0.29.0
aiosqlite==0.19.0
pydantic==2.5.0
python-dotenv==1.0.0
gunicorn==21.2.0


👤 Контакты

Разработчик: Сергей Молчанов
Email: molchan2025@gmail.com
GitHub: Sergey-Molchan

сам сайт https://www.lash-saundra.online
создан без регистрации для не большщого круга пользования