# from flask import Flask, request
# import requests
# import os
# from dotenv import load_dotenv
#
# load_dotenv()
# API_KEY = os.getenv("API_KEY")
#
# app = Flask(__name__)
#
#
# @app.route("/generate", methods=["POST"])
# def generate():
#     data = request.json
#
#     language = data.get("language", "")
#     errorMessage = data.get("errorMessage", "")
#     codeSnippet = data.get("codeSnippet", "")
#
#     prompt = f"""
# You are a senior software debugging expert.
#
# Analyze the error and code carefully.
#
# Return response in EXACT format below:
#
# Root Cause:
# <minimum 80 words detailed explanation>
#
# Fix Steps:
# <Numbered steps. Minimum 120 words total>
#
# What Not To Do:
# <Minimum 60 words. Common mistakes and prevention>
#
# LANGUAGE: {language}
# ERROR: {errorMessage}
# CODE:
# {codeSnippet}
# """
#
#     url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
#
#     payload = {
#         "contents": [{"parts": [{"text": prompt}]}],
#         "generationConfig": {
#             "temperature": 0,
#             "maxOutputTokens": 3000
#         }
#     }
#
#     try:
#         resp = requests.post(url, json=payload)
#
#         if resp.status_code != 200:
#             return "Root Cause:\nGemini API Error\n\nFix Steps:\nCheck API key or quota\n\nWhat Not To Do:\nDo not use invalid API credentials", 500
#
#         result = resp.json()
#         ai_text = result['candidates'][0]['content']['parts'][0]['text']
#
#         # Clean unwanted markdown if any
#         ai_text = ai_text.replace("```", "").strip()
#
#         return ai_text
#
#     except Exception as e:
#         return f"""Root Cause:
# {str(e)}
#
# Fix Steps:
# Ensure Flask AI service is running and reachable
#
# What Not To Do:
# Do not expose internal errors to users
# """, 500
#
#
# @app.route("/health", methods=["GET"])
# def health():
#     return {
#         "status": "healthy",
#         "model": "Gemini-2.5-flash"
#     }
#
#
# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000, debug=True)

from flask import Flask, request, Response
import requests
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

    prompt = f"""
You are a senior software debugging expert.

Analyze the error and code carefully.

RETURN EXACTLY PLAIN TEXT in the following format:

Root Cause:
<80+ words detailed explanation>

Fix Steps:
<120+ words, numbered step-by-step solution>

What Not To Do:
<60+ words common mistakes and prevention>

LANGUAGE: {language}
ERROR: {errorMessage}
CODE:
{codeSnippet}
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0, "maxOutputTokens": 3000}
    }

    try:
        resp = requests.post(url, json=payload)
        resp.raise_for_status()

        result = resp.json()
        ai_text = result['candidates'][0]['content']['parts'][0]['text']

        # Remove any Markdown or backticks
        ai_text = ai_text.replace("```", "").replace("```json", "").strip()

        # Return as plain text
        return Response(ai_text, mimetype='text/plain')

    except Exception as e:
        fallback = f"""
Root Cause:
{str(e)}

Fix Steps:
Ensure Flask AI service is running and reachable

What Not To Do:
Do not expose internal errors to users
"""
        return Response(fallback, mimetype='text/plain')


@app.route("/health", methods=["GET"])
def health():
    return {"status": "healthy", "model": "Gemini-2.5-flash"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
