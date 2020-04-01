import os
import traceback

from flask import Flask, redirect, render_template, request, session, url_for
from flask_github import GitHub

from openutils.handlers import HANDLERS

APP = Flask(__name__)

APP.config["GITHUB_CLIENT_ID"] = os.getenv("GITHUB_CLIENT_ID")
APP.config["GITHUB_CLIENT_SECRET"] = os.getenv("GITHUB_CLIENT_SECRET")
GITHUB = GitHub(APP)


@APP.route("/")
def index():
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


@APP.route("/github/login")
def github_login():
    return GITHUB.authorize(scope="user")


@APP.route("/github/callback")
@GITHUB.authorized_handler
def authorized(oauth_token):
    next_url = request.args.get("next") or url_for("index")
    if oauth_token is None:
        print("Authorization failed.")
        return redirect(next_url)
    session["github_access_token"] = oauth_token
    return redirect(next_url)


@GITHUB.access_token_getter
def token_getter():
    if "github_access_token" in session:
        return session["github_access_token"]
