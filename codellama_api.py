from flask import Flask, request, jsonify
import requests
import json
import re
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY")

app = Flask(__name__)


@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    language = data.get("language", "")
    errorMessage = data.get("errorMessage", "")
    codeSnippet = data.get("codeSnippet", "")

    prompt = f"""Analyze this exact error and code. Return ONLY valid JSON:

LANGUAGE: {language}
ERROR: {errorMessage}
CODE:
{codeSnippet}

{{"issue": "error type", "rootCause": "why it happens", "fixSteps": "1. step1\n2. step2", "whatNotToDo": "avoid this"}}"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 800
        }
    }

    try:
        resp = requests.post(url, json=payload)

        if resp.status_code == 200:
            result = resp.json()
            ai_text = result['candidates'][0]['content']['parts'][0]['text']

            # Extract JSON block
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', ai_text)
            if json_match:
                return jsonify(json.loads(json_match.group()))

            # Fallback parsing
            return jsonify({
                "issue": "AI response parsing",
                "rootCause": ai_text[:300],
                "fixSteps": "Manual analysis needed",
                "whatNotToDo": "Trust unparsed AI output"
            })
        else:
            return jsonify({
                "issue": f"API {resp.status_code}",
                "rootCause": resp.text[:200],
                "fixSteps": "New API key needed",
                "whatNotToDo": "Use expired keys"
            })

    except Exception as e:
        return jsonify({
            "issue": "Connection error",
            "rootCause": str(e),
            "fixSteps": "Check network",
            "whatNotToDo": "Offline API calls"
        })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "model": "Gemini-2.5-flash"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
