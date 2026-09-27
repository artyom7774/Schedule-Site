from flask import Flask, request, jsonify, render_template_string, render_template, g, redirect, url_for, abort

from src.variables import *

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
        <title>{{ name[0] }}</title>
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

    return render_template_string(text, name=NAME, log=log)


@app.route("/")
def index():
    return redirect(url_for("main", lang=language()))


@app.route("/<lang>/")
def main(lang):
    return render_template_string(load("main.html", "0"), name=NAME)


@app.route("/<lang>/documentation/")
def documentation(lang):
    return render_template_string(load("documentation.html", "0"), name=NAME)


@app.route("/<lang>/download/")
def download(lang):
    return render_template_string(load("download.html", "0"), name=NAME)


@app.route("/<lang>/service/")
def service(lang):
    return render_template_string(load("service.html", "0"), name=NAME)


@app.route("/<lang>/support/")
def support(lang):
    return render_template_string(load("support.html", "0"), name=NAME)


def start():
    write("-------------------- LOG --------------------")

    app.config["UPLOAD_FOLDER"] = "uploads"
    app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 ** 2

    app.run(host="0.0.0.0", debug=True, use_reloader=False)


if __name__ == "__main__":
    start()
