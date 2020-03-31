from openutils import bugtracker, github

HANDLERS = {
    "pr": github.handler,
    "bpo": bugtracker.handler,
}
