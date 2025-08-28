#!/usr/bin/env python3
"""
Setup configuration script for IT Internship Finder bot.
Run this after installing the package to configure the bot.
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any

# ANSI color codes
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
RED = "\033[0;31m"
NC = "\033[0m"  # No Color

def print_header():
    """Print the setup header."""
    print(f"{BLUE}=== IT Internship Finder Setup ==={NC}\n")
    print("This script will help you configure the IT Internship Finder bot.")
    print("You'll need to provide your Telegram bot token and set up Firebase.")
    print(f"{YELLOW}Note: Press Ctrl+C at any time to cancel the setup.{NC}\n")

def get_telegram_credentials() -> Dict[str, str]:
    """Get Telegram bot token and chat ID from user."""
    print(f"{BLUE}=== Telegram Bot Setup ==={NC}")
    print("1. Open Telegram and search for '@BotFather'")
    print("2. Send '/newbot' and follow the instructions")
    print("3. After creating the bot, BotFather will give you a token")
    print("4. To get your chat ID, send a message to @userinfobot on Telegram\n")
    
    while True:
        token = input("Enter your Telegram bot token: ").strip()
        if token and len(token) > 30:  # Basic validation
            break
        print(f"{RED}Invalid token. Please enter a valid Telegram bot token.{NC}")
    
    while True:
        chat_id = input("Enter your Telegram chat ID: ").strip()
        if chat_id and (chat_id.lstrip('-').isdigit() or chat_id.startswith('@')):
            break
        print(f"{RED}Invalid chat ID. Please enter a valid Telegram chat ID or username.{NC}")
    
    return {"TELEGRAM_BOT_TOKEN": token, "TELEGRAM_CHAT_ID": chat_id}

def setup_firebase() -> str:
    """Guide user through Firebase setup and return credentials path."""
    print(f"\n{BLUE}=== Firebase Setup ==={NC}")
    print("1. Go to https://console.firebase.google.com/")
    print("2. Create a new project or select an existing one")
    print("3. Go to Project Settings > Service Accounts")
    print("4. Click 'Generate New Private Key' and save the JSON file\n")
    
    while True:
        creds_path = input("Enter the path to your Firebase credentials JSON file: ").strip()
        if os.path.exists(creds_path):
            try:
                with open(creds_path) as f:
                    json.load(f)  # Validate JSON
                return creds_path
            except json.JSONDecodeError:
                print(f"{RED}Invalid JSON file. Please provide a valid Firebase credentials file.{NC}")
        else:
            print(f"{RED}File not found. Please enter a valid file path.{NC}")

def create_env_file(config: Dict[str, Any]) -> None:
    """Create or update the .env file with the provided configuration."""
    env_path = Path(".env")
    
    if env_path.exists():
        backup_path = Path(".env.bak")
        try:
            env_path.rename(backup_path)
            print(f"{YELLOW}Existing .env file backed up to .env.bak{NC}")
        except Exception as e:
            print(f"{YELLOW}Could not back up existing .env file: {e}{NC}")
    
    try:
        with open(env_path, "w") as f:
            f.write("# IT Internship Finder Configuration\n")
            for key, value in config.items():
                if value:
                    f.write(f'{key}="{value}"\n')
        
        print(f"\n{GREEN}✓ Configuration saved to .env{NC}")
    except Exception as e:
        print(f"{RED}Error writing to .env file: {e}{NC}")
        sys.exit(1)

def main():
    """Run the setup process."""
    try:
        print_header()
        
        # Get Telegram credentials
        telegram_creds = get_telegram_credentials()
        
        # Get Firebase credentials
        firebase_creds_path = setup_firebase()
        
        # Create config dictionary
        config = {
            **telegram_creds,
            "FIREBASE_CREDENTIALS": firebase_creds_path,
            "UPDATE_INTERVAL": "3600",  # 1 hour in seconds
            "LOG_LEVEL": "INFO"
        }
        
        # Create .env file
        create_env_file(config)
        
        print(f"\n{GREEN}✓ Setup completed successfully!{NC}")
        print(f"\nRun the bot using: {YELLOW}internship-finder{NC}")
        
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Setup cancelled by user.{NC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}An error occurred during setup: {e}{NC}")
        sys.exit(1)

if __name__ == "__main__":
    main()
