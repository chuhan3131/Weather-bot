# Погодник Бот

**Погодник** - Telegram бот для быстрого просмотра погоды через инлайн-режим. Показывает погоду в виде наглядных карточек с подробной информацией. Просто введите `@usernamebot` и название города в любом чате.

**Рабочая версия бота**: [t.me/chweatbot](https://t.me/chweatbot)

<img width="1601" height="1000" alt="Погодник Бот" src="https://github.com/user-attachments/assets/b924e4d7-c0b0-4a16-91a0-3531de5c535e" />

## 🚀 Возможности

- **Инлайн-режим работы** - работает в любом чате без запуска бота
- **Универсальный поиск** - поддержка городов, стран и IP-адресов  
- **Случайные локации** - команда `@chweatbot random` для случайного места
- **Визуальные карточки** - красивое графическое отображение погоды
- **Высокая производительность** - асинхронная обработка запросов

## 📦 Установка

1. **Установите зависимости**:
```bash
pip install -r requirements.txt
```

2. **Создайте файл `.env`**:
```env
BOT_TOKEN=your_telegram_bot_token
OPENWEATHERMAP_API_KEY=your_openweather_api_key
IMGBB_API_KEY=your_imgbb_api_key
```

3. **Запустите бота**:
```bash
python3 bot.py
```

## 💡 Использование

В любом чате Telegram просто введите:

```
@chweatbot Москва
@chweatbot London,GB
@chweatbot 8.8.8.8
@chweatbot random
```

## 🛠 Технологии

- **Aiogram 3.x** - современный фреймворк для Telegram ботов
- **Aiohttp** - асинхронные HTTP запросы
- **Pillow** - генерация графических карточек
- **OpenWeatherMap API** - данные о погоде

## 📁 Структура проекта

```
weatherman/
├── bot.py                 # Основной файл бота
├── config.py             # Конфигурация и переменные окружения
├── handlers/
│   └── inline.py         # Обработчики инлайн-запросов
├── utils/
│   ├── weather.py        # Работа с погодными API
│   ├── image_utils.py    # Генерация карточек погоды
│   └── file_utils.py     # Утилиты для работы с файлами
└── templates/            # Шаблоны изображений
```

## 🔑 Получение API ключей

- **Telegram Bot Token**: [@BotFather](https://t.me/BotFather)
- **OpenWeatherMap API**: [openweathermap.org](https://openweathermap.org/api)
- **ImgBB API**: [imgbb.com](https://api.imgbb.com/)

---

*Простой и эффективный способ узнать погоду в любом уголке мира*
