import pytest

import json
from items.models import Item, HistoryItem
from tests.fixtures.fixture_data import (
    create_file, create_folder, URL_DELETE,
    DATE_1, DATE_2, DATE_3, URL_IMPORTS,
    URL_NODES,
)
from collections import OrderedDict


@pytest.mark.django_db
def test_nodes_file_success(client):
    """
    Успешное получение информацию об файле по идентификатору. Для файла поле children равно null
    """
    #создаем элемент в БД
    item_1 = create_file(1, 1)
    Item.objects.create(
        id=item_1['id'],
        type=item_1['type'],
        size=item_1['size'],
        url=item_1['url'],
        date=DATE_1
    )
    cnt = Item.objects.count()
    assert cnt == 1

    id = item_1['id']
    response = client.get(
        URL_NODES + f'/{id}'
    )
    assert response.status_code == 200
    #добавим к словарю item_1 поля date и children и сравним с response
    item_1['date'] = DATE_1
    item_1['children'] = None
    assert response.data == item_1


@pytest.mark.django_db
def test_nodes_error_wrong_id(client):
    """
    Ошибка элемент не найден
    """
    #создаем элемент в БД
    item_1 = create_file(1, 1)
    Item.objects.create(
        id=item_1['id'],
        type=item_1['type'],
        size=item_1['size'],
        url=item_1['url'],
        date=DATE_1
    )
    cnt = Item.objects.count()
    assert cnt == 1

    id = 'wrong_file_id'
    response = client.get(
        URL_NODES + f'/{id}'
    )
    assert response.status_code == 404

@pytest.mark.django_db
def test_nodes_folder_success(client):
    """
    Успешное получение информацию об папке по идентификатору.
    При получении информации о папке также предоставляется информация о её дочерних элементах.
    Для пустой папки поле children равно пустому массиву
    """
    #создаем элемент в БД
    item_1 = create_folder(1, 1)
    item_2 = create_folder(2,1, parentId=item_1['id'])
    #создаем item_1
    Item.objects.create(
        id=item_1['id'],
        type=item_1['type'],
        size=item_1['size'],
        url=item_1['url'],
        date=DATE_1
    )
    # создаем item_2
    Item.objects.create(
        id=item_2['id'],
        type=item_2['type'],
        size=item_2['size'],
        url=item_2['url'],
        date=DATE_1,
        parent = Item.objects.get(id=item_1['id'])
    )

    #получим информацию о папке 1
    id = item_1['id']
    response = client.get(
        URL_NODES + f'/{id}'
    )
    assert response.status_code == 200
    #добавим к словарю item_1 и item_2 поля date и children и сравним с response
    #поменяем местами поле Date и size у item_2

    item_2['date'] = DATE_1
    item_2['size'] = item_2.pop('size')
    item_2['children'] = None
    item_1['date'] = DATE_1
    item_1['children'] = [OrderedDict(item_2)]

    assert response.data == item_1

@pytest.mark.django_db
def test_nodes_folder_size_equal_sum_of_childrens(client):
    """
    Размер папки - это суммарный размер всех её элементов.
    """
    # Добавлять элементы будем через POST запрос,
    # чтобы обновлялось поле size у папок
    item_1 = create_folder(1, 1)
    item_2 = create_file(2,1, parentId=item_1['id'], size=50)
    item_3 = create_file(2, 2, parentId=item_1['id'], size=30)

    payload = {"items": [item_1, item_2, item_3], "updateDate": DATE_1}

    response = client.post(
        URL_IMPORTS, json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 200

    #получим информацию о папке 1
    # ее size должен быть равен 50+30=80
    id = item_1['id']
    response = client.get(
        URL_NODES + f'/{id}'
    )
    assert response.status_code == 200
    assert response.data['id'] == item_1['id']
    assert response.data['size'] == 80
