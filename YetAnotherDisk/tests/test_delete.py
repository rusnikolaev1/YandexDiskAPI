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
)
from api.utils import convert_str_to_datetime
import datetime


@pytest.mark.django_db
def test_delete_success(client):
    """
    Успешное удаление элемента по идентификатору.
    """
    # создаем элемент в БД
    item_1 = create_file(1, 1)
    Item.objects.create(
        id=item_1["id"],
        type=item_1["type"],
        size=item_1["size"],
        url=item_1["url"],
        date=DATE_2,
    )
    cnt = Item.objects.count()
    assert cnt == 1
    # удаляем элемент запросом DELETE
    id = item_1["id"]
    response = client.delete(URL_DELETE + f"/{id}?date=" + DATE_1)
    assert response.status_code == 200
    cnt = Item.objects.count()
    assert cnt == 0


@pytest.mark.django_db
def test_delete_error_no_date(client):
    """
    Ошибка при удалении без указания даты
    """
    # создаем элемент в БД
    item_1 = create_file(1, 1)
    Item.objects.create(
        id=item_1["id"],
        type=item_1["type"],
        size=item_1["size"],
        url=item_1["url"],
        date=DATE_1,
    )
    cnt = Item.objects.count()
    assert cnt == 1
    # удаляем элемент запросом DELETE
    id = item_1["id"]
    response = client.delete(URL_DELETE + f"/{id}")
    assert response.status_code == 400
    cnt = Item.objects.count()
    assert cnt == 1


@pytest.mark.django_db
def test_delete_error_no_id(client):
    """
    Ошибка при удалении, если не указан id
    """
    # создаем элемент в БД
    item_1 = create_file(1, 1)
    Item.objects.create(
        id=item_1["id"],
        type=item_1["type"],
        size=item_1["size"],
        url=item_1["url"],
        date=DATE_1,
    )
    cnt = Item.objects.count()
    assert cnt == 1
    # удаляем элемент запросом DELETE
    id = item_1["id"]
    response = client.delete(URL_DELETE)
    # предполагаем ошибку 404, так как item = get_object_or_404(Item, id=item_pk)
    assert response.status_code == 404
    cnt = Item.objects.count()
    assert cnt == 1


@pytest.mark.django_db
def test_delete_error_wrong_id(client):
    """
    Ошибка при удалении, если не указан id
    """
    # создаем элемент в БД
    item_1 = create_file(1, 1)
    Item.objects.create(
        id=item_1["id"],
        type=item_1["type"],
        size=item_1["size"],
        url=item_1["url"],
        date=DATE_1,
    )
    cnt = Item.objects.count()
    assert cnt == 1
    # удаляем элемент запросом DELETE
    id = "wrong_file_id"
    response = client.delete(URL_DELETE + f"/{id}?date=" + DATE_1)
    # предполагаем ошибку 404, так как item = get_object_or_404(Item, id=item_pk)
    assert response.status_code == 404
    cnt = Item.objects.count()
    assert cnt == 1


@pytest.mark.django_db
def test_delete_folder_deletes_all_childs(client):
    """
    При удалении папки удаляются все дочерние элементы
    """
    # создаем элемент в БД
    item_1 = create_folder(1, 1)
    item_2 = create_folder(2, 1, parentId=item_1["id"])
    item_3 = create_file(3, 1, parentId=item_2["id"])
    # файл на уровке папки item_1 и без родителя
    item_4 = create_file(1, 1)
    for item in [item_1, item_2, item_3, item_4]:
        Item.objects.create(
            id=item["id"],
            type=item["type"],
            size=item["size"],
            url=item["url"],
            parent=Item.objects.get(id=item["parentId"]) if item["parentId"] else None,
            date=DATE_2,
        )
    cnt = Item.objects.count()
    assert cnt == 4
    # удаляем элемент item_1 запросом DELETE
    id = item_1["id"]
    response = client.delete(URL_DELETE + f"/{id}?date=" + DATE_1)
    assert response.status_code == 200
    # в БД должен остаться только item_4
    cnt = Item.objects.count()
    assert cnt == 1


@pytest.mark.django_db
def test_delete_item_history_unavailable(client):
    """
    Доступ к истории обновлений удаленного элемента невозможен.
    """
    # Добавим элемент в базу. Проверим, что элемент появился в исторической БД
    # Удалим и проверим будет ли доступна история
    item_1 = create_file(1, 1)
    payload = {"items": [item_1], "updateDate": DATE_2}

    response = client.post(
        URL_IMPORTS, json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 200
    # информация об элементе должна добавиться в БД исторических данных
    cnt = HistoryItem.objects.count()
    assert cnt == 1
    id = HistoryItem.objects.get(pk=1).itemId
    assert id == item_1["id"]

    # удаляем элемент
    response = client.delete(URL_DELETE + f"/{id}?date=" + DATE_1)
    assert response.status_code == 200
    # В таблице Item нет элементов
    cnt = Item.objects.count()
    assert cnt == 0
    # В таблице HistoryItem тоже нет элементов
    cnt = HistoryItem.objects.count()
    assert cnt == 0


@pytest.mark.django_db
def test_delete_file_parents_updates_date(client):
    """
    При удалении файла обновляется дата и размер у родительских папок
    """
    # создаем элемент в БД
    item_1 = create_folder(1, 1)
    item_2 = create_folder(2, 1, parentId=item_1["id"])
    item_3 = create_file(3, 1, parentId=item_2["id"])
    # файл на уровке папки item_1 и без родителя
    item_4 = create_file(1, 1)
    # добавим элементы через POST, чтобы у папок обновилась информация size
    payload = {"items": [item_1, item_2, item_3, item_4], "updateDate": DATE_2}

    response = client.post(
        URL_IMPORTS, json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 200
    cnt = Item.objects.count()
    assert cnt == 4
    # проверим что date в БД равно DATE_2
    assert Item.objects.get(id=item_1["id"]).date == convert_str_to_datetime(DATE_2)
    assert Item.objects.get(id=item_2["id"]).date == convert_str_to_datetime(DATE_2)
    assert Item.objects.get(id=item_4["id"]).date == convert_str_to_datetime(DATE_2)
    # проверим, что size item_1 и item_2 равен item_3['size']
    assert Item.objects.get(id=item_1["id"]).size == item_3["size"]
    assert Item.objects.get(id=item_2["id"]).size == item_3["size"]

    # удаляем файл item_3 запросом DELETE
    id = item_3["id"]
    response = client.delete(URL_DELETE + f"/{id}?date=" + DATE_1)
    assert response.status_code == 200
    # у объектов item_1 и item_2 должно обновиться поле date
    # у item_4 оно не изменится
    assert Item.objects.get(id=item_1["id"]).date == convert_str_to_datetime(DATE_1)
    assert Item.objects.get(id=item_2["id"]).date == convert_str_to_datetime(DATE_1)
    assert Item.objects.get(id=item_4["id"]).date == convert_str_to_datetime(DATE_2)
    # проверим, что size item_1 и item_2 равен 0
    assert Item.objects.get(id=item_1["id"]).size == 0
    assert Item.objects.get(id=item_2["id"]).size == 0


@pytest.mark.django_db
def test_delete_error_date_than_item_date(client):
    """
    Ошибка валидации, если в запросе передана дата меньшая чем последняя дата обновления элемента
    """
    # Добавим элемент в базу.
    item_1 = create_file(1, 1)
    Item.objects.create(
        id=item_1["id"],
        type=item_1["type"],
        size=item_1["size"],
        url=item_1["url"],
        date=DATE_1,
    )
    # Создаем время меньшее чем DATE_1
    dt_2 = (
        convert_str_to_datetime(DATE_1) + datetime.timedelta(microseconds=-1)
    ).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"

    # отправляем DELETE запрос
    id = item_1["id"]
    response = client.delete(URL_DELETE + f"/{id}?date=" + DATE_1)
    assert response.status_code == 400
    # В таблице Item по-прежнему 1 элемент
    cnt = Item.objects.count()
    assert cnt == 1
