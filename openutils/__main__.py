import os
import secrets
from argparse import ArgumentParser

from openutils.views import APP


def main():
    parser = ArgumentParser()
    parser.add_argument(
        "-H", "--host", help="Server host", default="0.0.0.0", type=str
    )
    parser.add_argument(
        "-P", "--port", help="Server port", default=8000, type=int
    )
    parser.add_argument(
        "-d", "--debug", help="Debug mode on/of", default=False, type=bool
    )
    server = parser.parse_args()
    APP.secret_key = os.getenv("FLASK_SECRET_KEY", secrets.token_urlsafe(64))
    APP.run(server.host, server.port, server.debug)


if __name__ == "__main__":
    main()
