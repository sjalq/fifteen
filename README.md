# Productivity Tracker

A simple Windows application that helps you track your productivity by prompting you every 15 minutes to reflect on what you've accomplished and what you plan to do next.

## Features

- Pops up every 15 minutes (at exact intervals like 10:00, 10:15, etc.)
- Asks you what you accomplished in the past 15 minutes
- Asks you what you aim to do in the next 15 minutes
- Records your answers in a JSON file for later review
- Always-on-top window so you don't miss it
- System tray icon shows when the app is running
- Minimal and unobtrusive UI

## Requirements

- Python 3.x
- tkinter (usually comes with Python)
- Pillow (PIL) library for image processing

## Installation

1. Make sure you have Python installed on your Windows machine. If not, download and install it from [python.org](https://python.org).

2. Clone or download this repository to your local machine.

## Usage

### Running the script directly

```
python productivity_tracker.py
```

### Creating a standalone executable

To create a standalone .exe file that doesn't require Python to be installed:

1. Install PyInstaller:
```
pip install pyinstaller
```

2. Create the executable:
```
pyinstaller --onefile --noconsole productivity_tracker.py
```

3. Find the executable in the `dist` folder and run it.

## Data Storage

Your productivity data is stored in a file called `productivity_log.json` in the same directory as the application. The data is structured as follows:

```json
{
    "2023-06-07 10:00": {
        "past_15": "Answered emails and scheduled meetings",
        "next_15": "Start working on project proposal"
    },
    "2023-06-07 10:15": {
        "past_15": "Outlined project proposal",
        "next_15": "Research competitors for the proposal"
    }
}
```

The timestamps in the JSON file (like "2023-06-07 10:00") reflect when the popup appeared, not when you submitted your response.

You can review this file anytime to see your productivity history.

## How It Works

- The application shows a system tray icon in the Windows notification area
- It displays a popup window immediately when launched
- It then runs in the background and calculates when the next 15-minute interval will occur.
- At each interval (like 10:00, 10:15, 10:30), it pops up a window again.
- Right-clicking the system tray icon allows you to show the popup or exit the application
- After you submit your answers, the popup window closes and waits for the next interval.
- If you close the popup window without submitting, it simply disappears until the next interval.
- The application continues running until you explicitly close it using the system tray icon's context menu.

## License

This project is open source and available under the MIT License. 