import traceback

from flask import Flask, render_template, request

from openutils.handlers import HANDLERS

APP = Flask(__name__)


@APP.route("/")
def hello():
    return render_template("index.html", error=None)


@APP.route("/query")
def query():
    if not all(
        field in request.args and request.args.get(field)
        for field in ("query", "type")
    ):
        return render_template("index.html", error="Fill the required fields")

    query = request.args["query"]
    platform = request.args["type"]
    extra = request.args.get("extra", None)
    if handler := HANDLERS.get(platform):
        try:
            return render_template(
                "results.html", results=tuple(handler(query, extra=extra))
            )
        except Exception as e:
            return render_template(
                "index.html",
                error="<br>".join(traceback.format_exc().splitlines()),
            )
    else:
        return render_template(
            "index.html", error="Please select a valid platform"
        )
