import pytest

import json
from items.models import Item, HistoryItem
from tests.fixtures.fixture_data import (
    create_file,
    create_folder,
    URL_DELETE,
    DATE_1,
    DATE_2,
    DATE_3,
    URL_IMPORTS,
    URL_NODES,
    URL_UPDATES,
)

from api.utils import convert_str_to_datetime
import datetime


@pytest.mark.django_db
def test_updates_file_success(client):
    """
    Успешное получение списка файлов, которые были обновлены
    за последние 24 часа включительно [date - 24h, date] от времени переданном в запросе.
    """
    # создаем элемент в БД
    item_1 = create_file(1, 1)
    # специально создаем папку, чтобы убедиться, что она не вернется в response
    item_2 = create_folder(1, 2)
    item_3 = create_file(1, 3)

    # item_1, item_2, item_2 добавим с датой DATE_1
    for item in [item_1, item_2, item_3]:
        Item.objects.create(
            id=item["id"],
            type=item["type"],
            size=item["size"],
            url=item["url"],
            parent=Item.objects.get(id=item["parentId"]) if item["parentId"] else None,
            date=DATE_1,
        )

    cnt = Item.objects.count()
    assert cnt == 3

    # GET запрос по адресу updates с параметром даты DATE_1
    response = client.get(URL_UPDATES + "?date=" + DATE_1)

    assert response.status_code == 200
    # В response должен вернуться  два файла, так как по условию этот endpoint возвращает только список файлов
    item_1["date"] = DATE_1
    item_3["date"] = DATE_1
    assert response.data == {"items": [item_1, item_3]}


@pytest.mark.django_db
def test_updates_file_success_only_24_hours(client):
    """
    Успешное получение списка файлов, которые были обновлены
    за последние 24 часа включительно [date - 24h, date] от времени переданном в запросе.
    """
    # создаем элемент в БД
    item_1 = create_file(1, 1)
    item_2 = create_file(1, 2)
    item_3 = create_file(1, 3)
    item_4 = create_file(1, 4)

    # item_1 добавим с датой DATE_1
    Item.objects.create(
        id=item_1["id"],
        type=item_1["type"],
        size=item_1["size"],
        url=item_1["url"],
        date=DATE_1,
    )
    # item_2 добавим со сдвигом от даты DATE_1 на 12 ч
    Item.objects.create(
        id=item_2["id"],
        type=item_2["type"],
        size=item_2["size"],
        url=item_2["url"],
        date=convert_str_to_datetime(DATE_1) + datetime.timedelta(hours=-12),
    )
    # item_3 добавим со сдвигом от даты DATE_1 на 1 микросекунду вперед
    Item.objects.create(
        id=item_3["id"],
        type=item_3["type"],
        size=item_3["size"],
        url=item_3["url"],
        date=convert_str_to_datetime(DATE_1)
        + datetime.timedelta(
            microseconds=1,
        ),
    )
    # item_4 добавим со сдвигом даты DATE_2 на 1 сутки и 1 микросекунда назад
    Item.objects.create(
        id=item_4["id"],
        type=item_4["type"],
        size=item_4["size"],
        url=item_4["url"],
        date=convert_str_to_datetime(DATE_1)
        - datetime.timedelta(days=-1, microseconds=-1),
    )

    cnt = Item.objects.count()
    assert cnt == 4

    # GET запрос по адресу updates с параметром даты DATE_1
    response = client.get(URL_UPDATES + "?date=" + DATE_1)

    assert response.status_code == 200
    # В response должен вернуться два файла item_1 и item_2
    item_1["date"] = DATE_1
    item_2["date"] = (
        convert_str_to_datetime(DATE_1) + datetime.timedelta(hours=-12)
    ).strftime("%Y-%m-%dT%H:%M:%S") + "Z"
    assert response.data == {"items": [item_1, item_2]}
