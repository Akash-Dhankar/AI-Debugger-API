from flask import Flask, request, jsonify
import requests
import json
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
    You are a senior software debugging assistant.

    Analyze the error and code below and return STRICT JSON only.

    Rules:
    - No markdown
    - No backticks
    - No explanations outside JSON
    - Do not leave fields empty

    LANGUAGE: {language}
    ERROR: {errorMessage}
    CODE:
    {codeSnippet}

    EXAMPLE OUTPUT FORMAT:

    {{
      "rootCause": "Short technical error type",
      "fixSteps": "1. Clear step one.\n2. Clear step two.\n3. Optional improvement.",
      "whatNotToDo": "Common mistakes to avoid."
    }}

    Now generate the JSON response.
    """

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0,
            "maxOutputTokens": 800
        }
    }

    try:
        resp = requests.post(url, json=payload)

        if resp.status_code != 200:
            return jsonify({
                "rootCause": resp.text[:200],
                "fixSteps": "Check API key or quota",
                "whatNotToDo": "Do not use invalid API credentials"
            })

        result = resp.json()
        ai_text = result['candidates'][0]['content']['parts'][0]['text']

        # 🧹 HARD CLEANUP (remove markdown if model ignores rules)
        ai_text = ai_text.replace("```json", "").replace("```", "").strip()

        # ✅ SAFE JSON PARSING (no regex)
        try:
            parsed = json.loads(ai_text)

            # Ensure required keys exist
            return jsonify({
                "rootCause": parsed.get("rootCause", "No root cause provided"),
                "fixSteps": parsed.get("fixSteps", "No fix steps provided"),
                "whatNotToDo": parsed.get("whatNotToDo", "No guidance provided")
            })

        except json.JSONDecodeError:
            # Fallback if AI returns malformed JSON
            return jsonify({
                "rootCause": ai_text[:800],
                "fixSteps": "Manual review required",
                "whatNotToDo": "Do not trust malformed AI output"
            })

    except Exception as e:
        return jsonify({
            "rootCause": str(e),
            "fixSteps": "Ensure Flask AI service is running and reachable",
            "whatNotToDo": "Do not expose internal errors to users"
        })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "model": "Gemini-2.5-flash"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
