import pytest
from rest_framework.test import APIClient

URL_IMPORTS = "/imports"
URL_DELETE = "/delete"
URL_NODES = "/nodes"
URL_UPDATES = "/updates"
URL_HISTORY_NODE = "/node"
DATE_1 = "2022-09-11T12:00:00Z"
DATE_2 = "2022-08-22T12:05:00Z"
DATE_3 = "2022-07-22T11:05:00Z"
NOT_ISO_DATE_1 = "2022/11/9 12:00:00"


@pytest.fixture
def client():
    return APIClient()


def create_file(depth, cnt, parentId=None, url="/", size=10):
    item = {
        "id": f"FILE_{depth}_{cnt}",
        "url": url,
        "type": "FILE",
        "parentId": parentId,
        "size": size,
    }
    print(item)
    return item


def create_folder(depth, cnt, parentId=None, url=None, size=None):
    item = {
        "id": f"FOLDER_{depth}_{cnt}",
        "url": url,
        "type": "FOLDER",
        "parentId": parentId,
        "size": size,
    }
    print(item)
    return item
