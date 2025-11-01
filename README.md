# 🌤️ Weather Bot

A Telegram bot that generates beautiful weather cards using inline mode.

<div align="center">

### 📸 Card Examples

<img width="400" height="250" alt="Day theme" src="https://github.com/user-attachments/assets/9fe51bae-96ee-455b-9cd7-df3134b87acc" />
<img width="400" height="250" alt="Night theme" src="https://github.com/user-attachments/assets/730333bf-d658-4979-a85f-fd7e376d2413" />

*Day and night themes switch automatically based on the time of day*

</div>

## 🚀 Quick Start

```bash
git clone https://github.com/chuhan3131/Weather-bot.git
cd Weather-bot
pip install -r requirements.txt
```

Create a `.env` file:

```env
BOT_TOKEN=your_telegram_bot_token
OPENWEATHERMAP_API_KEY=your_openweather_api_key
IMGBB_API_KEY=your_imgbb_api_key
```

Run the bot:

```bash
python bot.py
```

## 💡 Usage

In any Telegram chat:

* `@your_bot Moscow` — weather in a city
* `@your_bot 8.8.8.8` — weather by IP address
* `@your_bot random` — random location

## ✨ Features

* 🌞 **Day theme** (09:01–22:59) — light interface
* 🌙 **Night theme** (23:00–09:00) — dark interface
* 🎨 **Automatic emojis** — different icons for day and night
* 📱 **Beautiful cards** with full weather information
* 🌍 **Supports** cities and IP addresses
* 🎲 **Random locations** for exploration

## 🛠 Technologies

* Python 3.8+
* Aiogram 3.x
* Pillow (image generation)
* OpenWeatherMap API
* Asynchronous programming
