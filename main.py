from flask import Flask, request, jsonify, render_template_string, render_template

from src.variables import *

app = Flask(__name__)

log = ""


def write(*args):
    global log

    line = ' '.join([str(element) for element in args])
    log += f"{line}\n"

    print(line)


@app.route("/log")
def logger():
    global log

    text = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{ title }}</title>
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

    return render_template_string(text, title=TITLE, log=log)


@app.route("/")
def site():
    return render_template("index.html", title=TITLE, name=NAME, description=DESCRIPTION)


def start():
    write("-------------------- LOG --------------------")

    app.config["UPLOAD_FOLDER"] = "uploads"
    app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 ** 2

    app.run(host="0.0.0.0", debug=True, use_reloader=False)


if __name__ == "__main__":
    start()
