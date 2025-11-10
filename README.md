# Chinese Article Reader Assistant

A web application that helps users read Chinese articles by providing pinyin and definitions when hovering over phrases.

## Features

- Input Chinese text in a text area
- Process text to identify phrases
- Hover over phrases to see pinyin and English definitions
- Clean, modern UI with smooth interactions

## Setup

### Prerequisites

- Python 3.7 or higher
- A web browser

### Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Start the Python backend server:
```bash
python app.py
```

The server will start on `http://localhost:5000`

3. Open your browser and go to:
```
http://localhost:5000
```

The Flask server serves both the frontend (HTML/CSS/JS) and the backend API, so everything works together automatically.

## Current Status

- ✅ Frontend UI with text input and reading area
- ✅ Hover tooltips for phrases
- ✅ Basic Python Flask backend structure
- ⏳ Chinese text processing (to be implemented)
- ⏳ Pinyin generation (to be implemented)
- ⏳ Definition lookup (to be implemented)

## Next Steps

The backend (`app.py`) currently has placeholder functionality. Future implementation will include:

1. Chinese text segmentation (using libraries like `jieba`)
2. Pinyin conversion (using libraries like `pypinyin`)
3. Dictionary/definition lookup (using APIs or local dictionaries)

## Project Structure

```
chinese-reader/
├── index.html      # Main HTML file
├── styles.css      # Styling
├── app.js          # Frontend JavaScript
├── app.py          # Python Flask backend
├── requirements.txt # Python dependencies
└── README.md       # This file
```
