# Chat With OS (Linux)

[![Python](https://img.shields.io/badge/Python-3.x-blue.svg)](https://www.python.org/)
[![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey)](https://www.sqlite.org/)
[![Typer](https://img.shields.io/badge/CLI-Typer-green)](https://typer.tiangolo.com/)
[![Gemini AI](https://img.shields.io/badge/Gemini-AI-yellow)](https://example.com/gemini-ai)

## Description
This terminal application allows you to interact with OS resources using natural language through a command-line interface. It leverages Gemini AI for natural language processing and SQLite for data storage. The application supports scheduled tasks to manage and store data efficiently.


## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Features](#features)

## Installation

Follow the steps below to set up the project locally:

```bash
# Clone the repository
git clone https://github.com/RoboJunior/chat-with-os.git

# Navigate into the project directory
cd chat-with-os

# Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows, use venv\Scripts\activate

#Export your gemini-api-key
EXPORT GOOGLE_API_KEY = XXXX (or) add the key to your .env file 

# Install required packages
pip install -r requirements.txt
```
## Usage
Run the application from the terminal to interact with OS resources using natural language commands:

```bash
#Start the application
python main.py --help

#Example command to chat with OS resources
python main.py chat-with-os "What is the current CPU usage?"

#Example command to the schedule a job defaults to (* * * * *)
python main.py schedule-cron-job --schedule_time "* 1 * * *" 

#Example command to reschedule a job defaults to (* 1 * * *)
python main.py reschedule-cron-job --reschedule-time "* 2 * * *"

#Example command to remove a job
python main.py remove-cron-job   
```

## Features
- Natural Language Interface: Interact with OS resources using natural language commands.
- SQLite Storage: Store and manage data efficiently using SQLite.
- Scheduled Tasks: Automatically handle data management on a schedule.
- Gemini AI Integration: Utilize Gemini AI for natural language processing and enhanced functionalities.
- Typer CLI: A user-friendly command-line interface built with Typer.

