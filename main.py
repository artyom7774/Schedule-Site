from flask import Flask, request, jsonify, render_template_string, render_template, g, redirect, url_for, abort

from src.chat import requestAI

import requests
import json
import os

app = Flask(__name__)

log = ""

cookies = {
    "lang": {
        "name": "lang",
        "default": "ru",
        "support": ["ru"],
        "time": 10 * 60 * 60 * 24 * 365
    }
}

BASE = os.path.dirname(os.path.abspath(__file__))

files = json.load(open(os.path.join(BASE, "files.json"), "r", encoding="utf-8"))

prompts = {
    "base": open(os.path.join(BASE, "prompts", "base.txt"), "r", encoding="utf-8").read(),
    "request": open(os.path.join(BASE, "prompts", "request.txt"), "r", encoding="utf-8").read()
}

def write(*args):
    global log

    line = ' '.join([str(element) for element in args])
    log += f"{line}\n"

    print(line)


def language():
    return getattr(g, "lang", None) or request.cookies.get(cookies["lang"]["name"], cookies["lang"]["default"])


@app.before_request
def detect():
    url = (request.view_args or {}).get("lang")
    query = request.args.get("lang")

    if url:
        if url not in cookies["lang"]["support"]:
            abort(404)

        g.lang = url

        return

    if query:
        if query not in cookies["lang"]["support"]:
            abort(404)

        g.lang = query

        return

    lang = request.cookies.get(cookies["lang"]["name"])

    g.lang = lang if lang in cookies["lang"]["support"] else cookies["lang"]["default"]


@app.after_request
def save_lang_cookie(response):
    lang = getattr(g, "lang", None)

    if lang in cookies["lang"]["support"]:
        response.set_cookie(cookies["lang"]["name"], lang, max_age=cookies["lang"]["time"], samesite="Lax", httponly=True)

    return response


def load(name, index):
    lang = language()

    dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", lang)

    if not os.path.exists(dir):
        lang = cookies["lang"]["default"]
        dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", lang)

        g.lang = lang

    with open(os.path.join(dir, name), encoding="utf-8") as f:
        template = f.read()

    with open(os.path.join(dir, "base", "header.html"), encoding="utf-8") as f:
        template = template.replace("%HEADER%", f.read())

    with open(os.path.join(dir, "base", "footer.html"), encoding="utf-8") as f:
        template = template.replace("%FOOTER%", f.read())

    template = template.replace("$LANGUAGE$", lang)

    return template


@app.route("/log")
def logger():
    global log

    text = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>СуперЗавуч</title>
        <link rel="stylesheet" href="{{ url_for('static', filename='css/log.css') }}">
    </head>
    <body>
        <style>
          pre {
            color: #FFFFFF;
          }
        </style>
        <pre>{{ log }}</pre>
    </body>
    </html>
    """

    return render_template_string(text, log=log)


@app.route("/")
def index():
    return redirect(url_for("main", lang=language()))


@app.route("/<lang>/")
def main(lang):
    return render_template_string(load("main.html", "0"))


@app.route("/<lang>/documentation/")
def documentation(lang):
    return render_template_string(load("documentation.html", "0"))


@app.route("/<lang>/download/")
def download(lang):
    return render_template_string(load("download.html", "0"))


@app.route("/<lang>/community/")
def community(lang):
    return render_template_string(load("community.html", "0"))


def question(message, history=None):
    history = history or []

    text = ""

    for element in history:
        text += element["role"] + ": " + element["content"]

    history = text + "\n" + message

    links = ""

    for i, file in enumerate(files):
        links += f"{file['name'].replace('X', str(i), 1)}\n"

    indexes = requestAI(prompts["request"].replace("%HISTORY%", history).replace("%MESSAGE%", message).replace("%LINKS%", links))

    assert indexes[0] == 0

    print(">", *list(map(int, indexes[1].split())))

    indexes = indexes[1]

    text = ""

    for index in list(map(int, indexes.split())):
        text += f"------------------------------ {files[index]['name'].replace('X', str(index), 1)} ------------------------------\n"

        if "value" not in files[index]:
            if files[index]["get"][0] == "file":
                files[index]["value"] = open(os.path.join(BASE, files[index]["get"][1]), "r", encoding="utf-8").read()

            if files[index]["get"][0] == "download":
                files[index]["value"] = requests.get(files[index]["get"][1]).text

        text += files[index]["value"] + "\n"

    responce = prompts["base"].replace("%HISTORY%", history).replace("%MESSAGE%", message).replace("%FILES%", text)

    return requestAI(responce)[1]


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}

    message = (data.get("message") or "").strip()
    history = data.get("history") or []

    if not isinstance(history, list):
        history = []

    history = [element for element in history if isinstance(element, dict) and element.get("role") in ("user", "assistant") and isinstance(element.get("content"), str)]

    try:
        reply = question(message, history)

    except Exception as e:
        return jsonify({"error": f"{e}"}), 500

    return jsonify({"reply": reply})


def start():
    write("-------------------- LOG --------------------")

    app.config["UPLOAD_FOLDER"] = "uploads"
    app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 ** 2

    app.run(host="0.0.0.0", debug=True, use_reloader=False)


if __name__ == "__main__":
    start()
