import pytest
from dateutil.parser import isoparse

import json
from items.models import Item
from tests.fixtures.fixture_data import (
    create_file,
    create_folder,
    URL_IMPORTS,
    DATE_1,
    DATE_2,
    DATE_3,
    NOT_ISO_DATE_1,
)


@pytest.mark.django_db
def test_import_success(client):
    """
    Успешный импорт элемента, с заполненными полями
    """
    # импорт файла
    item_1 = create_file(1, 1)
    payload = {"items": [item_1], "updateDate": DATE_1}

    response = client.post(
        URL_IMPORTS, json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 200
    # импорт папки
    item_2 = create_folder(1, 1)
    payload = {"items": [item_2], "updateDate": DATE_1}

    response = client.post(
        URL_IMPORTS, json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 200

    cnt = Item.objects.count()
    assert cnt == 2


@pytest.mark.django_db
def test_import_error_duplicates(client):
    """
    - id элементов в одном запросе импорта не должны повторяться
    - в одном запросе не может быть двух элементов с одинаковым id
    """
    item_1 = create_file(1, 1)
    payload = {
        "items": [
            item_1,
            item_1,
        ],
        "updateDate": DATE_1,
    }

    response = client.post(
        URL_IMPORTS, json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 400
    cnt = Item.objects.count()
    assert cnt == 0


@pytest.mark.django_db
def test_import_error_id_null(client):
    """
    поле id не может быть равно null
    """
    item_1 = create_file(1, 1)
    item_1["id"] = None
    payload = {
        "items": [
            item_1,
        ],
        "updateDate": DATE_1,
    }

    response = client.post(
        URL_IMPORTS, json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 400
    cnt = Item.objects.count()
    assert cnt == 0


@pytest.mark.django_db
def test_import_error_parent_not_folder(client):
    """
    Родителем элемента может быть только папка
    """
    item_1 = create_file(1, 1)
    item_2 = create_file(1, 1, parentId=item_1["id"])
    payload = {
        "items": [
            item_1,
        ],
        "updateDate": DATE_1,
    }

    response = client.post(
        URL_IMPORTS, json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 200
    cnt = Item.objects.count()
    assert cnt == 1

    payload = {
        "items": [
            item_2,
        ],
        "updateDate": DATE_1,
    }
    response = client.post(
        URL_IMPORTS, json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 400
    cnt = Item.objects.count()
    assert cnt == 1


@pytest.mark.django_db
def test_import_parent_change_to_none(client):
    """
    Элементы могут не иметь родителя (при обновлении parentId на null элемент остается без родителя)
    """
    item_1 = create_folder(1, 1)
    item_2 = create_file(1, 1, parentId=item_1["id"])
    payload = {
        "items": [item_1, item_2],
        "updateDate": DATE_2,
    }
    response = client.post(
        URL_IMPORTS, json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 200
    parent = Item.objects.get(id=item_2["id"]).parent
    assert parent.id == item_1["id"]
    # меняем parentId на null
    item_2["parentId"] = None
    payload = {
        "items": [item_2],
        "updateDate": DATE_1,
    }
    response = client.post(
        URL_IMPORTS, json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 200
    parent = Item.objects.get(id=item_2["id"]).parent
    assert parent == None


@pytest.mark.django_db
def test_import_error_folder_with_url(client):
    """
    поле url при импорте папки всегда должно быть равно null
    """
    item_1 = create_folder(1, 1, url="/")
    payload = {
        "items": [item_1],
        "updateDate": DATE_1,
    }
    response = client.post(
        URL_IMPORTS, json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_import_error_url_more_than_255(client):
    """
    размер поля url при импорте файла всегда должен быть меньше либо равным 255
    """
    item_1 = create_file(1, 1, url=("/" * 256))
    payload = {
        "items": [item_1],
        "updateDate": DATE_1,
    }

    response = client.post(
        URL_IMPORTS, json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_import_error_folder_with_size(client):
    """
    поле size при импорте папки всегда должно быть равно null
    """
    item_1 = create_folder(1, 1, size=10)
    payload = {
        "items": [item_1],
        "updateDate": DATE_1,
    }

    response = client.post(
        URL_IMPORTS, json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_import_error_file_size_zero(client):
    """
    поле size для файлов всегда должно быть больше 0
    """
    item_1 = create_file(1, 1, size=0)
    payload = {
        "items": [item_1],
        "updateDate": DATE_1,
    }

    response = client.post(
        URL_IMPORTS, json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_import_error_file_size_null(client):
    """
    поле size для файлов всегда должно быть больше 0
    """
    item_1 = create_file(1, 1, size=None)
    payload = {
        "items": [item_1],
        "updateDate": DATE_1,
    }

    response = client.post(
        URL_IMPORTS, json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_import_update_all_file_fields(client):
    """
    - при обновлении элемента обновленными считаются все их параметры
    - при обновлении параметров элемента обязательно обновляется поле date в соответствии с временем обновления
    """
    item_1 = create_file(1, 1)
    payload = {
        "items": [item_1],
        "updateDate": DATE_3,
    }

    response = client.post(
        URL_IMPORTS, json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 200

    db_item_1 = Item.objects.get(id=item_1["id"])
    assert db_item_1.url == "/"
    assert db_item_1.size == 10
    assert db_item_1.parent == None

    assert db_item_1.date == isoparse(DATE_3)

    # создадим родителя
    item_2 = create_folder(1, 1)
    payload = {
        "items": [item_2],
        "updateDate": DATE_2,
    }
    response = client.post(
        URL_IMPORTS, json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 200

    # изменим item_1
    item_1["url"] = "/updated_url"
    item_1["size"] = 20
    item_1["parentId"] = item_2["id"]
    payload = {
        "items": [item_1],
        "updateDate": DATE_1,
    }
    response = client.post(
        URL_IMPORTS, json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 200

    db_item_1.refresh_from_db()
    # db_item_1 = Item.objects.get(id=item_1['id'])
    assert db_item_1.url == "/updated_url"
    assert db_item_1.size == 20
    assert db_item_1.parent.id == item_2["id"]
    assert db_item_1.date == isoparse(DATE_1)


@pytest.mark.django_db
def test_import_error_date_not_ISO_format(client):
    """
    дата обрабатывается согласно ISO 8601 (такой придерживается OpenAPI).
     Если дата не удовлетворяет данному формату, ответом будет код 400.
    """
    item_1 = create_file(1, 1)
    payload = {
        "items": [item_1],
        "updateDate": NOT_ISO_DATE_1,
    }
    print(payload)
    response = client.post(
        URL_IMPORTS, json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 400

    payload["updateDate"] = DATE_1
    response = client.post(
        URL_IMPORTS, json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_import_error_using_old_date(client):
    """
    Ошибка при попытке обновить элемент с указанием старой даты
    """
    item_1 = create_file(1, 1)
    payload = {
        "items": [item_1],
        "updateDate": DATE_1,
    }
    response = client.post(
        URL_IMPORTS, json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 200
    # при попытке обновить элемент с DATE_1 вернется ошибка 400
    payload["updateDate"] = DATE_1
    response = client.post(
        URL_IMPORTS, json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 400
