"""
Chinese Article Reader Assistant - Backend API
This will be implemented later with proper Chinese text processing.
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from text_processor import process_chinese_text
from dictionary import ChineseDictionary
from pathlib import Path
import requests
import zipfile
import os

app = Flask(__name__, static_folder='.')
CORS(app)  # Enable CORS for frontend communication

if not Path('resources/cedict_ts.u8').exists():
    print("Downloading CC-CEDICT dictionary...")
    response = requests.get('https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.zip')
    with open('resources/cedict_1_0_ts_utf-8_mdbg.zip', 'wb') as f:
        f.write(response.content)
    print("Unzipping dictionary...")
    with zipfile.ZipFile('resources/cedict_1_0_ts_utf-8_mdbg.zip', 'r') as zip_ref:
        zip_ref.extractall('resources')
    print("Dictionary downloaded and unzipped successfully")
    print("deleting zip file...")
    os.remove('resources/cedict_1_0_ts_utf-8_mdbg.zip')
    print("zip file deleted successfully")

# Initialize dictionary at startup - this loads it once when the app starts
print("Initializing Chinese dictionary...")
dictionary = ChineseDictionary()
print("Dictionary ready!")

# API routes must come before catch-all routes
@app.route('/api/process', methods=['POST'])
def process_text():
    """
    API endpoint to process Chinese text and return phrases with pinyin and definitions.
    """
    data = request.get_json()
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    result = process_chinese_text(text, dictionary)
    return jsonify(result)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'Chinese Reader API is running'})

# Serve the main HTML file
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# Serve static files (CSS, JS) - must come after API routes
@app.route('/<path:filename>')
def static_files(filename):
    # Don't serve API routes
    if filename.startswith('api/'):
        return jsonify({'error': 'Not found'}), 404
    # Only serve specific static files
    if filename in ['styles.css', 'app.js']:
        return send_from_directory('.', filename)
    return jsonify({'error': 'Not found'}), 404

if __name__ == '__main__':
    print("Starting Chinese Reader Assistant...")
    print("Open your browser and go to: http://localhost:5000")
    print("API endpoint: http://localhost:5000/api/process")
    app.run(debug=True, port=5000)
