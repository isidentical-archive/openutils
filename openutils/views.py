import json
import os
import secrets
import traceback
from urllib.request import Request, urlopen

from flask import Flask, redirect, render_template, request, session, url_for
from flask_github import GitHub

from openutils.handlers import HANDLERS

APP = Flask(__name__)

APP.config["SESSION_TYPE"] = "filesystem"
APP.config["GITHUB_CLIENT_ID"] = os.getenv("GITHUB_CLIENT_ID")
APP.config["GITHUB_CLIENT_SECRET"] = os.getenv("GITHUB_CLIENT_SECRET")
APP.secret_key = os.getenv("FLASK_SECRET_KEY", secrets.token_urlsafe(64))

GITHUB = GitHub(APP)


@APP.route("/")
def index():
    if (authorization := session.get("authorization")) is not None:
        if authorization:
            error = "Successfully logged in!"
        else:
            error = "Couldn't logged in!"

    return render_template("index.html", error=None)


@APP.route("/query")
def query():
    if not all(
        field in request.args and request.args.get(field)
        for field in ("query", "type")
    ):
        return render_template("index.html", error="Fill the required fields")

    extra = dict(request.args)
    query = extra.pop("query")
    platform = extra.pop("type")
    if handler := HANDLERS.get(platform):
        try:
            return render_template(
                "results.html",
                results=tuple(handler(query, session, extra=extra)),
            )
        except Exception as e:
            return render_template(
                "index.html",
                error="<br>".join(traceback.format_exc().splitlines()),
            )
    else:
        return render_template(
            "index.html", error="Please select a valid platform",
        )


@APP.route("/github/login")
def github_login():
    return GITHUB.authorize(scope="user")


@APP.route("/github/logout")
def github_logout():
    session["authorization"] = None
    session["github_access_token"] = None
    return redirect("/")


@APP.route("/github/callback")
@GITHUB.authorized_handler
def authorized(oauth_token):
    next_url = request.args.get("next") or url_for("index")
    if oauth_token is None:
        print("Authorization failed.")
        session["authorization"] = False
        return redirect(next_url)

    session["authorization"] = True
    session["github_access_token"] = oauth_token
    return redirect(next_url)
