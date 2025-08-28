"""
Configuration settings for the IT Internship Finder.
"""
import os
from typing import Dict, List

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Firebase configuration
FIREBASE_CREDENTIALS = os.getenv("FIREBASE_CREDENTIALS", "serviceAccountKey.json")

# RSS Feed URLs for different job boards
RSS_FEEDS = {
    "We Work Remotely": "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    "RemoteOK": "https://remoteok.io/remote-dev-jobs.rss",
    "StackOverflow Jobs": "https://stackoverflow.com/jobs/feed?tags=internship",
    "EuroTechJobs": "https://www.eurotechjobs.com/jobs/rss/internship",
}

# Web scraping configurations
WEB_SCRAPERS = {
    "internshala": {
        "enabled": True,
        "max_pages": 3,  # Number of pages to scrape
    },
    "remoteok": {
        "enabled": True,
        "max_retries": 3,
        "timeout": 30.0
    },
    "remotive": {
        "enabled": True,
        "max_retries": 3,
        "timeout": 30.0
    },
    "wwr": {
        "enabled": True,
        "max_retries": 3,
        "timeout": 30.0
    }
}

# Keywords to filter IT-related internships
IT_KEYWORDS = [
    # Programming languages
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "ruby", "php", "swift", "kotlin", "rust",
    "scala", "r", "matlab", "perl", "dart", "haskell", "lua", "groovy", "elixir", "clojure", "julia",
    
    # Web development
    "web", "frontend", "front-end", "backend", "back-end", "full stack", "full-stack", "react", "angular",
    "vue", "node", "django", "flask", "spring", "laravel", "ruby on rails", "express", "asp.net", "graphql",
    "rest", "api", "microservices", "serverless",
    
    # Mobile development
    "mobile", "android", "ios", "react native", "flutter", "xamarin", "swiftui", "kotlin multiplatform",
    
    # Data science and AI/ML
    "data science", "machine learning", "artificial intelligence", "ai", "ml", "deep learning", "neural networks",
    "nlp", "natural language processing", "computer vision", "data analysis", "data engineering", "big data",
    "tensorflow", "pytorch", "keras", "scikit-learn", "pandas", "numpy", "opencv", "spark", "hadoop",
    
    # DevOps and Cloud
    "devops", "cloud", "aws", "amazon web services", "azure", "google cloud", "gcp", "docker", "kubernetes",
    "terraform", "ansible", "jenkins", "github actions", "gitlab ci", "ci/cd", "infrastructure as code",
    "serverless", "lambda", "google cloud functions", "azure functions",
    
    # Other IT-related
    "cybersecurity", "information security", "penetration testing", "ethical hacking", "blockchain",
    "ethereum", "smart contracts", "solidity", "iot", "internet of things", "embedded systems",
    "game development", "unity", "unreal engine", "vr", "virtual reality", "ar", "augmented reality",
    "quantum computing", "robotics", "automation", "sre", "site reliability engineering",
    
    # General terms
    "software", "developer", "engineering", "programming", "coding", "development", "computer science",
    "cs", "it", "information technology", "tech", "technology", "computer", "computing", "digital"
]

# Location filters (empty list means all locations)
LOCATION_FILTERS = [
    "india",  # Filter for India internships only
]

# Internship duration filters (in months, 0 means no preference)
MIN_DURATION = 0  # Minimum duration in months (0 = no minimum)
MAX_DURATION = 12  # Maximum duration in months (0 = no maximum)

# Logging configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "formatter": "standard",
            "class": "logging.StreamHandler",
        },
        "file": {
            "level": "DEBUG",
            "formatter": "standard",
            "class": "logging.FileHandler",
            "filename": "internship_finder.log",
        },
    },
    "loggers": {
        "": {  # root logger
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": True
        },
    },
}

# Request settings
REQUEST_TIMEOUT = 30  # seconds
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Database settings
DATABASE_SETTINGS = {
    "collection_name": "internships",
    "batch_size": 100,  # Number of records to process in a batch
}

# Notification settings
NOTIFICATION_SETTINGS = {
    "max_notifications_per_batch": 10,  # Max number of internships to include in a single notification
    "notification_format": "markdown",  # or "html" or "plain"
    "include_description": False,  # Whether to include full description in notifications
}

# Scheduler settings (for GitHub Actions)
SCHEDULER_SETTINGS = {
    "interval_hours": 5,  # How often to run the bot (in hours)
    "timezone": "UTC",   # Timezone for scheduling
}
