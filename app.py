"""
Chinese Article Reader Assistant - Backend API
This will be implemented later with proper Chinese text processing.
"""

import base64

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from botocore.exceptions import BotoCoreError, ClientError

from text_processor import process_chinese_text
from resources.utils import init_dictionary
from utils.aws import get_polly_client


app = Flask(__name__)
CORS(
    app, resources={r"/api/*": {"origins": "*"}}
)  # Enable CORS for frontend communication

dictionary = init_dictionary()


# API routes must come before catch-all routes
@app.route("/api/process", methods=["POST", "OPTIONS"])
def process_text():
    """
    API endpoint to process Chinese text and return phrases with pinyin and definitions.
    """
    data = request.get_json()
    text = data.get("text", "")

    if not text:
        return jsonify({"error": "No text provided"}), 400

    result = process_chinese_text(text)
    return jsonify(result)


@app.route("/api/health", methods=["GET", "OPTIONS"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok", "message": "Chinese Reader API is running"})


@app.route("/api/read-aloud", methods=["POST", "OPTIONS"])
def read_aloud():
    """
    Convert processed text into speech using AWS Polly and return as base64 audio.
    """
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()

    if not text:
        return jsonify({"error": "No text provided"}), 400

    try:
        polly = get_polly_client()
    except Exception as exc:  # pragma: no cover - surface initialization errors
        return (
            jsonify(
                {
                    "error": "Failed to initialize AWS Polly client",
                    "details": str(exc),
                }
            ),
            500,
        )

    voice_id = "Zhiyu"
    language_code = "cmn-CN"
    engine = "neural"

    synthesize_kwargs = {
        "Text": text,
        "OutputFormat": "mp3",
        "VoiceId": voice_id,
    }

    if language_code:
        synthesize_kwargs["LanguageCode"] = language_code

    if engine:
        synthesize_kwargs["Engine"] = engine

    try:
        response = polly.synthesize_speech(**synthesize_kwargs)
    except (BotoCoreError, ClientError) as exc:
        return (
            jsonify(
                {
                    "error": "AWS Polly synthesis failed",
                    "details": str(exc),
                }
            ),
            500,
        )

    audio_stream = response.get("AudioStream")
    if not audio_stream:
        return jsonify({"error": "No audio stream returned from AWS Polly"}), 500

    with audio_stream:
        audio_bytes = audio_stream.read()

    if not audio_bytes:
        return jsonify({"error": "AWS Polly returned empty audio"}), 500

    audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

    return jsonify(
        {
            "audio": audio_base64,
            "contentType": response.get("ContentType", "audio/mpeg"),
        }
    )


# Serve the main HTML file
@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    print("Starting Chinese Reader Assistant...")
    print("Open your browser and go to: http://localhost:5000")
    print("API endpoint: http://localhost:5000/api/process")
    app.run(debug=True, port=5000)
