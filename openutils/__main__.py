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
    server = parser.parse_args()
    APP.run(server.host, server.port)


if __name__ == "__main__":
    main()
