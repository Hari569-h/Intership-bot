# 🚀 IT Internship Finder Bot

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

An automated bot that finds and notifies you about the latest IT internships from various job boards and RSS feeds. Built with Python, Firebase Firestore, and Telegram.

## ✨ Features

- 🔍 Scrapes multiple job boards for IT internships
- 📱 Sends real-time notifications via Telegram
- 🔄 Automatically checks for new internships (configurable interval)
- 🚫 Prevents duplicate notifications
- 💾 Stores seen internships in Firebase Firestore
- 🌍 Supports global and India-specific job boards
- 🛠️ Easy to extend with new sources

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/it-internship-finder.git
   cd it-internship-finder
   ```

2. **Create and activate a virtual environment:**
   ```bash
   # On Windows
   python -m venv venv
   .\venv\Scripts\activate
   
   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## 🔧 Configuration

1. **Set up environment variables:**
   - Copy `.env.example` to `.env`
   - Fill in your Telegram bot token and chat ID
   - Configure Firebase credentials (see below)

2. **Telegram Bot Setup:**
   - Talk to [@BotFather](https://t.me/botfather) on Telegram
   - Create a new bot with `/newbot`
   - Save the API token
   - Get your chat ID by sending a message to your bot and visiting:
     ```
     https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
     ```

3. **Firebase Setup:**
   - Go to [Firebase Console](https://console.firebase.google.com/)
   - Create a new project
   - Go to Project Settings > Service Accounts
   - Click "Generate New Private Key" and save the JSON file
   - Place the JSON file in the project root as `serviceAccountKey.json`

## 🚀 Usage

### Running Locally

```bash
python main.py
```

### Running with Docker

```bash
docker build -t it-internship-finder .
docker run --env-file .env it-internship-finder
```

### GitHub Actions (Recommended)

The bot is configured to run automatically via GitHub Actions every 2 hours. To set this up:

1. Fork this repository
2. Add the following secrets to your repository:
   - `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
   - `TELEGRAM_CHAT_ID`: Your Telegram chat ID
   - `FIREBASE_CREDENTIALS_JSON`: The contents of your Firebase service account JSON file (entire JSON as a string)
3. Push your code to GitHub

The workflow will automatically:
- Run every 2 hours
- Cache and persist the seen_urls.json file between runs
- Commit and push any changes to seen_urls.json back to your repository

## 🏗️ Project Structure

```
it-internship-finder/
├── .github/workflows/      # GitHub Actions workflows
├── src/                    # Source code
│   ├── fetchers/           # Job board fetchers
│   ├── models/             # Data models
│   ├── services/           # External services
│   └── utils/              # Utility functions
├── tests/                  # Unit tests
├── .env.example           # Example environment variables
├── .gitignore
├── main.py                # Main entry point
├── README.md
├── requirements.txt
└── setup.py               # Setup script
```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a new branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests: `pytest`
5. Format code: `black .`
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- All the amazing open-source projects that made this possible
- The job boards for providing internship data
- The Python community for their awesome libraries
# Intership-bot
