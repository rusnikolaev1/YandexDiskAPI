import pytest

import json
from items.models import Item, HistoryItem
from tests.fixtures.fixture_data import (
    create_file, create_folder, URL_DELETE,
    DATE_1, DATE_2, DATE_3, URL_IMPORTS,
    URL_NODES,URL_UPDATES, URL_HISTORY_NODE,
    NOT_ISO_DATE_1
)

from api.utils import convert_str_to_datetime
import datetime

@pytest.mark.django_db
def test_history_node_file_success(client):
    """
    Успешное получение истории обновлений по файлу за заданный полуинтервал [from, to).
    """
    # создаем элемент в БД
    item_1 = create_file(1, 1)
    payload = {"items": [item_1], "updateDate": DATE_1}

    response = client.post(
        URL_IMPORTS, json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 200

    #меняем дату и повторно отправляем POST
    dt_2 = convert_str_to_datetime(DATE_1) + datetime.timedelta(hours=1, microseconds=1)
    payload['updateDate'] = dt_2.strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
    response = client.post(
        URL_IMPORTS, json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 200


    # меняем дату и еще раз отправляем POST
    dt_3 = convert_str_to_datetime(DATE_1) + datetime.timedelta(hours=4, microseconds=1)
    payload['updateDate'] = dt_3.strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
    response = client.post(
        URL_IMPORTS, json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 200

    #В таблице Item должен быть 1 элемент, а в HistoryItem - 3
    assert Item.objects.count() == 1
    assert HistoryItem.objects.count() == 3

    #GET запрос по адресу /node/{id}/history с параметром даты DATE_1 - dt3
    # должнен вернуть 2 записи, так как фильтрация по полуинтервалу
    id = item_1['id']

    response = client.get(
        URL_HISTORY_NODE + f'/{id}/history' + '?dateStart=' + DATE_1 + '&dateEnd=' + dt_3.strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
    )

    assert response.status_code == 200
    #В response должен вернуться две версии item_1 с временем DATE_1 и dt2
    item_1_ver_1 = item_1.copy()
    item_1_ver_2 = item_1.copy()
    item_1_ver_1['date'] = DATE_1
    item_1_ver_2['date'] = dt_2.strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
    assert response.data == [item_1_ver_2, item_1_ver_1]

@pytest.mark.django_db
def test_history_node_file_success(client):
    """
    Успешное получение истории обновлений по папке за заданный полуинтервал [from, to).
    Размер папки - это суммарный размер всех её элементов
    """
    # создаем элемент в БД
    item_1 = create_folder(1, 1)
    item_2 = create_file(1, 1, parentId=item_1['id'], size = 50)
    item_3 = create_file(1,2, parentId=item_1['id'], size = 50)
    # сначала создадим item_1, а потом по очереди item_2 и item_3
    # в результате в таблице HistoryItem должно будет получиться 3 записи для item_1
    payload = {"items": [item_1], "updateDate": DATE_3}

    response = client.post(
        URL_IMPORTS, json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 200

    payload = {"items": [item_2], "updateDate": DATE_2}

    response = client.post(
        URL_IMPORTS, json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 200
    print(json.dumps(payload))

    payload = {"items": [item_3], "updateDate": DATE_1}

    response = client.post(
        URL_IMPORTS, json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 200
    print(json.dumps(payload))

    #проверяем, что в таблице HistoryItem есть 3 записи для item_1
    assert HistoryItem.objects.filter(itemId=item_1['id']).count() == 3

    #GET запрос по адресу /node/{id}/history с параметром даты DATE_3 - DATE_1+микросекунда, чтобы в ответе вернулись все три записи
    id = item_1['id']
    dtStart = DATE_3
    dtEnd = (convert_str_to_datetime(DATE_1) + datetime.timedelta(microseconds=1)).strftime('%Y-%m-%dT%H:%M:%S.%f') + 'Z'
    response = client.get(
        URL_HISTORY_NODE + f'/{id}/history' + '?dateStart=' + dtStart + '&dateEnd=' + dtEnd
    )

    assert response.status_code == 200
    #В response должен вернуться две версии item_1 с временем DATE_3, DATE_2, DATE_1
    # у первой записи размер None, у второй - 50, у третьей 100
    item_1_ver_1 = item_1.copy()
    item_1_ver_2 = item_1.copy()
    item_1_ver_3 = item_1.copy()
    item_1_ver_1['date'] = DATE_3
    item_1_ver_1['size'] = None
    item_1_ver_2['date'] = DATE_2
    item_1_ver_2['size'] = 50
    item_1_ver_3['date'] = DATE_1
    item_1_ver_3['size'] = 100
    assert response.data == [ item_1_ver_3, item_1_ver_2, item_1_ver_1]


@pytest.mark.django_db
def test_history_node_error_item_not_found(client):
    """
    Ошибка элемент не найден.
    """
    # создаем элемент в БД
    item_1 = create_file(1, 1)
    # сначала создадим item_1
    payload = {"items": [item_1], "updateDate": DATE_1}

    response = client.post(
        URL_IMPORTS, json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 200
    # проверим, что в HistoryItem появилась запись
    assert HistoryItem.objects.count() == 1
    # GET запрос по адресу /node/{id}/history
    id = 'wrong_file_id'
    response = client.get(
        URL_HISTORY_NODE + f'/{id}/history' + '?dateStart=' + DATE_1 + '&dateEnd=' + DATE_1
    )
    assert response.status_code == 404

@pytest.mark.django_db
def test_history_node_error_wrong_date(client):
    """
    Ошибка валидации, если указана неверная дата
    """
    # создаем элемент в БД
    item_1 = create_file(1, 1)
    # сначала создадим item_1
    payload = {"items": [item_1], "updateDate": DATE_1}

    response = client.post(
        URL_IMPORTS, json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 200
    # проверим, что в HistoryItem появилась запись
    assert HistoryItem.objects.count() == 1
    # GET запрос по адресу /node/{id}/history
    id = item_1['id']
    response = client.get(
        URL_HISTORY_NODE + f'/{id}/history' + '?dateStart=' + NOT_ISO_DATE_1 + '&dateEnd=' + NOT_ISO_DATE_1
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_history_node_error_deleted_items(client):
    """
    История по удаленным элементам недоступна.
    """
    # создаем элемент в БД
    item_1 = create_file(1, 1)
    # сначала создадим item_1
    payload = {"items": [item_1], "updateDate": DATE_1}

    response = client.post(
        URL_IMPORTS, json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 200
    # проверим, что в HistoryItem появилась запись
    assert HistoryItem.objects.count() == 1
    #удалим элемент через DELETE запрос
    id = item_1['id']
    dt_2 = (convert_str_to_datetime(DATE_1) + datetime.timedelta(microseconds=1)).strftime('%Y-%m-%dT%H:%M:%S.%f') + 'Z'
    response = client.delete(
        URL_DELETE + f'/{id}?date=' + dt_2
    )

    # GET запрос по адресу /node/{id}/history
    dt_3 = (convert_str_to_datetime(DATE_1) + datetime.timedelta(microseconds=2)).strftime('%Y-%m-%dT%H:%M:%S.%f') + 'Z'
    response = client.get(
        URL_HISTORY_NODE + f'/{id}/history' + '?dateStart=' + DATE_1 + '&dateEnd=' + dt_3
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_history_node_without_date_return_all_history(client):
    """
    Если не указаны параметры dateStart и dateEnd можно получить статистику за всё время
    """
    # создаем элемент в БД
    item_1 = create_file(1, 1)
    # сначала создадим item_1
    payload = {"items": [item_1], "updateDate": DATE_1}

    response = client.post(
        URL_IMPORTS, json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 200
    #добавляем 1 час ко времени DATE_1 и обновляем элемент
    dt_2 = (convert_str_to_datetime(DATE_1) + datetime.timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S.%f') + 'Z'
    payload['updateDate'] = dt_2
    response = client.post(
        URL_IMPORTS, json.dumps(payload), content_type="application/json"
    )

    # добавляем еще 1 час ко времени dt_2 и обновляем элемент
    dt_3 = (convert_str_to_datetime(dt_2) + datetime.timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S.%f') + 'Z'
    payload['updateDate'] = dt_3
    response = client.post(
        URL_IMPORTS, json.dumps(payload), content_type="application/json"
    )

    # проверим, что в HistoryItem есть 3 записи
    assert HistoryItem.objects.count() == 3

    # GET запрос по адресу /node/{id}/history
    id = item_1['id']
    response = client.get(
        URL_HISTORY_NODE + f'/{id}/history' + '?dateStart=' + DATE_1 + '&dateEnd=' + dt_3
    )
    assert response.status_code == 200
    # при указании dateStart=DATE_1 и dateEnd=dt_3 вернется 2 элемента
    # так как данные возвращаются за полуинтервал полуинтервал [from, to)
    assert len(response.data) == 2

    # теперь отправим запрос без даты
    # должны вернуться все записи, то есть 3
    response = client.get(
        URL_HISTORY_NODE + f'/{id}/history'
    )
    assert len(response.data) == 3