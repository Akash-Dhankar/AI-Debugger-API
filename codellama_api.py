import os

os.environ["HF_HOME"] = "A:/hf_cache"
os.environ["HF_HUB_CACHE"] = "A:/hf_cache/hub"
os.environ["TRANSFORMERS_CACHE"] = "A:/hf_cache/transformers"
os.makedirs("A:/hf_cache", exist_ok=True)
print("✅ Cache set to A:/hf_cache")

from flask import Flask, request, jsonify
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

app = Flask(__name__)
HF_TOKEN = os.getenv("HF_TOKEN")
MODEL_NAME = "bigcode/starcoderbase-1b"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, token=HF_TOKEN)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    token=HF_TOKEN,
    torch_dtype=torch.float32,
    device_map="cpu",
    low_cpu_mem_usage=True,
    trust_remote_code=True
)

@app.route("/generate", methods=["POST"])
def generate():
    try:
        data = request.json
        prompt = data.get("prompt", "")
        max_new_tokens = data.get("max_tokens", 128)
        temperature = data.get("temperature", 0.7)

        if not prompt:
            return jsonify({"error": "Prompt is required"}), 400

        inputs = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True)

        inputs = {k: v.to("cpu") for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id,
                repetition_penalty=1.1
            )

        generated = tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[-1]:],
            skip_special_tokens=True
        )

        return jsonify({
            "generated_text": generated.strip(),
            "model": MODEL_NAME,
            "success": True
        })
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "model": MODEL_NAME,
        "device": "CPU"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
