import csv
import re
import shelve
import xmlrpc.client
from pathlib import Path
from urllib.request import urlretrieve

ARTIFACTS = Path(__file__).parent / "handlers" / "bugtracker"
if not ARTIFACTS.exists():
    ARTIFACTS.mkdir()

DOWNLOAD_URL = "https://bugs.python.org/issue?@action=export_csv&@columns=id,activity,title,creator,assignee,status,type&@sort=-activity&@filter=status&@pagesize=50&@startwith=0&status=-1,1,2,3"


class BPOTransformer(xmlrpc.client.SafeTransport):
    def send_content(self, connection, request_body):
        connection.putheader("Referer", "https://bugs.python.org/")
        connection.putheader("Origin", "https://bugs.python.org")
        connection.putheader("X-Requested-With", "XMLHttpRequest")
        super().send_content(connection, request_body)


def get_xml_rpc_proxy():
    proxy = xmlrpc.client.ServerProxy(
        "https://bugs.python.org/xmlrpc",
        allow_none=True,
        verbose=True,
        transport=BPOTransformer(),
    )
    return proxy


def filter_issues(query):
    query = re.compile(query, re.I)
    with open(ARTIFACTS / "all_issues.csv") as issues:
        reader = csv.DictReader(issues)
        for row in reader:
            if row["status"] != "1":
                continue
            if query.search(row["title"]):
                yield row


def refresh_data():
    print("Refreshing the data...")
    urlretrieve(DOWNLOAD_URL, ARTIFACTS / "all_issues.csv")
    print("Data updated successfully")


def handler(query, extra=None):
    if extra is not None and "refresh" in extra:
        refresh_data()
    issues = filter_issues(query)
    issue_shelf = shelve.open(str(ARTIFACTS / "issues.db"), writeback=True)
    proxy = get_xml_rpc_proxy()

    issue_metadata = {}
    for issue in issues:
        issue_id = issue["id"]
        if issue_id not in issue_shelf:
            issue_shelf[issue_id] = proxy.display(f"issue{issue_id}")
        issue_metadata[issue_id] = issue_shelf[issue_id]

    issue_shelf.close()

    issue_metadata = [
        (issue, metadata)
        for issue, metadata in issue_metadata.items()
        if len(metadata["pull_requests"]) + len(metadata["files"]) == 0
    ]

    issue_metadata = sorted(
        issue_metadata, key=lambda pack: len(pack[1]["messages"])
    )
    for issue, metadata in issue_metadata:
        yield {
            "link": f"https://bugs.python.org/issue{issue}",
            "title": f"bpo-{issue}: {metadata['title']}",
            "metadata": {
                "messages": len(metadata["messages"]),
                "nosy": len(metadata["nosy"]),
            },
        }


if __name__ == "__main__":
    main()
