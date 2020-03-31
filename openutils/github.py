import json
import os
import webbrowser
from pathlib import Path
from urllib.request import Request, urlopen

ARTIFACTS = Path(__file__).parent / "handlers" / "github"
if not ARTIFACTS.exists():
    ARTIFACTS.mkdir()

API_BASE = "https://api.github.com"
MAX_PAGES = 20
QUERY = """
{
  repository(name: "cpython", owner: "python") {
    pullRequests(first: 100,%s states: OPEN) {
      nodes {
        files(first: 10) {
          nodes {
            path
          }
        }
        url
        title
      }
      pageInfo {
        endCursor
      }
    }
  }
}
"""


def send_query(query, token):
    data = json.dumps({"query": query}).encode()
    request = Request(
        f"{API_BASE}/graphql",
        data=data,
        headers={"Authorization": f"token {token}"},
    )
    with urlopen(request) as page:
        return json.load(page)


def valid_data(data):
    if "errors" in data:
        return False
    elif data["data"]["repository"] is None:
        return False
    elif data["data"]["repository"]["pullRequests"] is None:
        return False
    elif len(data["data"]["repository"]["pullRequests"]["nodes"]) == 0:
        return False
    return True


def get_fresh_data(token):
    after = ""
    results = []
    while len(results) == 0 or valid_data(results[-1]):
        if len(results) > 0:
            end = results[-1]["data"]["repository"]["pullRequests"][
                "pageInfo"
            ]["endCursor"]
            after = ' after: "%s",' % end

        results.append(send_query(QUERY % after), token)
        print(f"Crawling the {len(results)}th page.")

    results.pop()
    return results


def dump_results(results):
    pull_requests = []
    for result in results:
        for pull_request in result["data"]["repository"]["pullRequests"][
            "nodes"
        ]:
            pull_requests.append(
                {
                    "files": [
                        changed_file["path"]
                        for changed_file in pull_request["files"]["nodes"]
                    ],
                    "title": pull_request["title"],
                    "url": pull_request["url"],
                }
            )
    with open(ARTIFACTS / "results.json", "w") as cache:
        json.dump(pull_requests, cache)


def get_prs():
    with open(ARTIFACTS / "results.json") as cache:
        yield from json.load(cache)


def handler(query, extra=None):
    if extra is not None:
        results = get_fresh_data(extra)
        dump_results(results)

    max_files = float("inf")
    exact = False

    query_files = query.split()
    for file in query_files.copy():
        if file.startswith("max-files:"):
            query_files.remove(file)
            max_files = int(file[len("max-files:") :])
        elif file == "!exact":
            query_files.remove(file)
            exact = True

    for result in get_prs():
        files = result["files"]
        matches = []
        for query_file in query_files:
            for result_file in result["files"]:
                if exact and query_file == result_file:
                    matches.append(result_file)
                if (
                    not exact
                    and query_file.casefold() in result_file.casefold()
                ):
                    matches.append(result_file)

        if len(matches) == 0:
            continue

        if len(result["files"]) > max_files:
            continue

        yield {
            "link": result["url"],
            "title": result["title"],
            "metadata": {file: file in result["files"] for file in query_files}
            if exact
            else {file: None for file in result["files"]},
        }


if __name__ == "__main__":
    main()
