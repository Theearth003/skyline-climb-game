from flask import Flask, jsonify, request, send_from_directory
from urllib.parse import quote_plus
import re

app = Flask(__name__, static_folder="public", static_url_path="")

@app.get("/")
def index():
    return send_from_directory("public", "index.html")

@app.get("/health")
def health():
    return jsonify({"ok": True, "service": "PublicTrace"})

def normalize_phone(value):
    raw = (value or "").strip()
    digits = re.sub(r"\D", "", raw)
    if digits.startswith("234"):
        local = "0" + digits[3:]
        intl = "+" + digits
    elif digits.startswith("0"):
        local = digits
        intl = "+234" + digits[1:]
    else:
        local = digits
        intl = "+234" + digits
    return raw, local, intl

@app.get("/api/phone")
def phone_search():
    raw, local, intl = normalize_phone(request.args.get("q", ""))
    if len(re.sub(r"\D", "", local)) < 7:
        return jsonify({"ok": False, "error": "Enter a valid phone number."}), 400

    variants = [local, intl, intl.replace("+", ""), local.replace("0", "+234", 1) if local.startswith("0") else local]
    variants = list(dict.fromkeys(variants))
    quoted = " OR ".join(f'"{v}"' for v in variants)

    engines = [
        {"name":"Google Web","url":"https://www.google.com/search?q="+quote_plus(quoted)},
        {"name":"Bing Web","url":"https://www.bing.com/search?q="+quote_plus(quoted)},
        {"name":"Google News","url":"https://www.google.com/search?tbm=nws&q="+quote_plus(quoted)},
        {"name":"Google Images","url":"https://www.google.com/search?tbm=isch&q="+quote_plus(quoted)}
    ]
    social = [
        ("Instagram", "instagram.com"),
        ("Facebook", "facebook.com"),
        ("TikTok", "tiktok.com"),
        ("X", "x.com"),
        ("LinkedIn", "linkedin.com"),
        ("YouTube", "youtube.com")
    ]
    social_results = [
        {"name": name, "url": "https://www.google.com/search?q="+quote_plus(quoted+" site:"+domain)}
        for name, domain in social
    ]
    return jsonify({
        "ok": True,
        "input": raw,
        "local": local,
        "international": intl,
        "searches": engines,
        "social": social_results
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
