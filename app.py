"""
Chinese Article Reader Assistant - Backend API
This will be implemented later with proper Chinese text processing.
"""

import base64
import logging
import re
import unicodedata
from collections import defaultdict
from dotenv import load_dotenv

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from botocore.exceptions import BotoCoreError, ClientError

from text_processor import process_chinese_text
from resources.utils import init_dictionary
from utils.aws import get_polly_client

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(
    app, resources={r"/api/*": {"origins": "*"}}
)  # Enable CORS for frontend communication

# Configure rate limiting
limiter = Limiter(
    app=app, key_func=get_remote_address, default_limits=["200 per day", "50 per hour"]
)

# Configure caching
cache = Cache(
    app,
    config={
        "CACHE_TYPE": "simple",  # Use 'redis' for production
        "CACHE_DEFAULT_TIMEOUT": 3600,  # 1 hour default
    },
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# IP-based usage tracking for monitoring
ip_usage = defaultdict(lambda: defaultdict(int))
suspicious_ips = set()

# Request size limits
MAX_PROCESS_TEXT_LENGTH = 5000  # characters for text processing
MAX_SPEECH_TEXT_LENGTH = 2000  # characters for speech synthesis

dictionary = init_dictionary()


def validate_chinese_text(text):
    """
    Validate that text contains mostly Chinese characters and is not malicious.
    """
    if not text or not isinstance(text, str):
        return False, "Text must be a non-empty string"

    # Remove whitespace for length checks
    text_stripped = text.strip()

    if len(text_stripped) == 0:
        return False, "Text cannot be empty"

    # Check for excessive non-Chinese characters (potential spam)
    chinese_chars = sum(
        1 for char in text_stripped if unicodedata.category(char) == "Lo"
    )
    total_chars = len(re.sub(r"\s+", "", text_stripped))  # Remove whitespace

    if total_chars > 0 and chinese_chars / total_chars < 0.1:
        return False, "Text must contain at least 10% Chinese characters"

    # Check for suspicious patterns (repeated characters, etc.)
    if re.search(r"(.)\1{50,}", text_stripped):  # 50+ repeated characters
        return False, "Text contains suspicious repeated characters"

    return True, None


def log_request_info():
    """Log request information for monitoring."""
    ip = request.remote_addr
    endpoint = request.endpoint

    if endpoint and endpoint.startswith("api."):
        ip_usage[ip][endpoint] += 1

        # Check for suspicious activity
        total_requests = sum(ip_usage[ip].values())
        if total_requests > 100:  # Threshold for suspicious activity
            if ip not in suspicious_ips:
                suspicious_ips.add(ip)
                logger.warning(
                    f"Suspicious activity detected from IP: {ip} (total requests: {total_requests})"
                )


def check_request_size(text, max_length, endpoint_name):
    """Check if request text exceeds size limits."""
    if len(text) > max_length:
        logger.warning(
            f"Request size limit exceeded for {endpoint_name}: {len(text)} chars from {request.remote_addr}"
        )
        return (
            False,
            f"Text too long. Maximum {max_length} characters allowed for {endpoint_name}",
        )
    return True, None


# Request logging and monitoring
@app.before_request
def before_request():
    log_request_info()


# API routes must come before catch-all routes
@app.route("/api/process", methods=["POST", "OPTIONS"])
@limiter.limit("10 per minute; 100 per hour")  # More permissive for text processing
def process_text():
    """
    API endpoint to process Chinese text and return phrases with pinyin and definitions.
    Includes rate limiting, size limits, and input validation.
    """
    try:
        data = request.get_json()
        text = data.get("text", "").strip()

        # Basic validation
        if not text:
            return jsonify({"error": "No text provided"}), 400

        # Size limit check
        size_ok, size_error = check_request_size(
            text, MAX_PROCESS_TEXT_LENGTH, "text processing"
        )
        if not size_ok:
            return jsonify({"error": size_error}), 400

        # Content validation
        valid, validation_error = validate_chinese_text(text)
        if not valid:
            return jsonify({"error": validation_error}), 400

        # Process text
        result = process_chinese_text(text)
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error processing text from {request.remote_addr}: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/health", methods=["GET", "OPTIONS"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok", "message": "Chinese Reader API is running"})


@app.route("/api/stats", methods=["GET", "OPTIONS"])
def get_stats():
    """Get usage statistics for monitoring."""
    # Only allow access from localhost for security
    if request.remote_addr not in ["127.0.0.1", "localhost", "::1"]:
        return jsonify({"error": "Access denied"}), 403

    total_requests = sum(
        sum(endpoint_counts.values()) for endpoint_counts in ip_usage.values()
    )

    return jsonify(
        {
            "total_requests": total_requests,
            "unique_ips": len(ip_usage),
            "suspicious_ips": list(suspicious_ips),
            "top_ips": sorted(
                [(ip, sum(counts.values())) for ip, counts in ip_usage.items()],
                key=lambda x: x[1],
                reverse=True,
            )[:10],  # Top 10 IPs by request count
            "endpoint_usage": {
                endpoint: sum(
                    ip_counts.get(endpoint, 0) for ip_counts in ip_usage.values()
                )
                for endpoint in ["api.process_text", "api.read_aloud"]
            },
        }
    )


@app.route("/api/read-aloud", methods=["POST", "OPTIONS"])
@limiter.limit("5 per minute; 20 per hour")  # More restrictive due to AWS Polly costs
@cache.cached(timeout=7200, query_string=True)  # Cache audio for 2 hours
def read_aloud():
    """
    Convert processed text into speech using AWS Polly and return as base64 audio.
    Includes rate limiting, caching, size limits, and input validation.
    """
    try:
        data = request.get_json(silent=True) or {}
        text = (data.get("text") or "").strip()

        # Basic validation
        if not text:
            return jsonify({"error": "No text provided"}), 400

        # Size limit check (stricter for expensive Polly calls)
        size_ok, size_error = check_request_size(
            text, MAX_SPEECH_TEXT_LENGTH, "speech synthesis"
        )
        if not size_ok:
            return jsonify({"error": size_error}), 400

        # Content validation
        valid, validation_error = validate_chinese_text(text)
        if not valid:
            return jsonify({"error": validation_error}), 400

        # AWS Polly processing
        try:
            polly = get_polly_client()
        except Exception as exc:
            logger.error(
                f"Failed to initialize Polly client for {request.remote_addr}: {str(exc)}"
            )
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

        # Use neural engine for longer texts (more expensive but better quality)
        if len(text) > 10:
            engine = "neural"
        else:
            engine = "standard"

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
            logger.error(
                f"Polly synthesis failed for {request.remote_addr}: {str(exc)}"
            )
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

    except Exception as e:
        logger.error(
            f"Error in read-aloud endpoint from {request.remote_addr}: {str(e)}"
        )
        return jsonify({"error": "Internal server error"}), 500


# Serve the main HTML file
@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    print("Starting Chinese Reader Assistant...")
    print("Open your browser and go to: http://localhost:5000")
    print("API endpoint: http://localhost:5000/api/process")
    app.run(debug=True, port=5000)
