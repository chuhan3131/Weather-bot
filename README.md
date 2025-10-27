
# 🌤️ Weather Bot

Telegram бот для красивых погодных карточек работающий через inline режим.

<div align="center">
  
### 📸 Примеры карточек
<img width="400" height="250" alt="Дневная тема" src="https://github.com/user-attachments/assets/9fe51bae-96ee-455b-9cd7-df3134b87acc" />
<img width="400" height="250" alt="Ночная тема" src="https://github.com/user-attachments/assets/730333bf-d658-4979-a85f-fd7e376d2413" />

*Дневная и ночная темы автоматически переключаются по времени*

</div>

## 🚀 Быстрый старт

```bash
git clone https://github.com/chuhan3131/Weather-bot.git
cd Weather-bot
pip install -r requirements.txt
```

Создайте файл `.env`:
```env
BOT_TOKEN=your_telegram_bot_token
OPENWEATHERMAP_API_KEY=your_openweather_api_key
IMGBB_API_KEY=your_imgbb_api_key
```

Запуск:
```bash
python bot.py
```

## 💡 Использование

В любом чате Telegram:
- `@ваш_бот Москва` - погода в городе
- `@ваш_бот 8.8.8.8` - погода по IP-адресу  
- `@ваш_бот random` - случайная локация

## ✨ Особенности

- 🌞 **Дневная тема** (09:01-22:59) - светлый интерфейс
- 🌙 **Ночная тема** (23:00-09:00) - тёмный интерфейс
- 🎨 **Автоматические эмодзи** - разные иконки для дня и ночи
- 📱 **Красивые карточки** с полной информацией о погоде
- 🌍 **Поддержка** городов и IP-адресов
- 🎲 **Случайные локации** для исследования

## 🛠 Технологии

- Python 3.8+
- Aiogram 3.x
- Pillow (генерация картинок)
- OpenWeatherMap API
- Асинхронное программирование
