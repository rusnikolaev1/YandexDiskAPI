from django.shortcuts import get_object_or_404
from django.http import Http404
from .serializers import ItemSerializer, HistoryItemSerializer
from items.models import Item, HistoryItem
from rest_framework import generics
from django.db import transaction
from rest_framework.response import Response
from rest_framework import status
from .filters import UpdatesFilter, HistoryFilter
from django_filters import rest_framework as filters
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.exceptions import ParseError
from .utils import update_size, convert_str_to_datetime
import datetime
from .throttle import GetRequestsRateThrottle, PostDeleteRequestsRateThrottle


@api_view(["POST"])
@throttle_classes([PostDeleteRequestsRateThrottle])
def item_imports(request):
    """
    Импорт элементов файловой системы
    """

    # проверки
    if not 'items' in request.data:
        raise ParseError('Отсутствует поле Items')
    if not request.data['items']:
        raise ParseError('Поле Items не может быть пустым')
    id_list = []
    request_list = request.data['items']
    for item in request_list:
        if not 'id' in item:
            raise ParseError('Поле id не может быть пустым')
        id_list.append(item["id"])
    if len(id_list) != len(set(id_list)):
        raise ParseError("Есть повторяющиеся элементы")
    #проверим наличие даты и ее формат
    if not 'updateDate' in request.data:
        raise ParseError("Отсутствует поле updateDate")
    date = convert_str_to_datetime(request.data["updateDate"])
    if not date:
        raise ParseError("Неверный формат даты")
    step = 0
    with transaction.atomic():
        while len(request_list) > 0:
            item = request_list[step]
            # если указан родитель и его нет в базе, то повышаем step и переходим к следующему item
            if "parentId" in item.keys():
                if item["parentId"]:
                    parent = Item.objects.filter(id=item["parentId"]).first()
                    if not parent:
                        # если родителя нет в базе и нет в списке , то Error
                        if not item["parentId"] in id_list:
                            raise ParseError("Должен быть указан существующий parentId")
                        else:
                            step += 1
                            continue
                else:
                    parent = None
            else:
                parent = None
            # проверяем указана ли цена
            if "size" in item.keys():
                if item["size"] == "":
                    item["size"] = None
            else:
                item["size"] = None

            # проверяем существует ли этот объект item
            src = Item.objects.filter(id=item["id"]).first()
            item["date"] = date
            if not src:
                serializer = ItemSerializer(data=item)
            else:
                serializer = ItemSerializer(src, data=item)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            if parent:
                src = Item.objects.filter(id=item["id"]).first()
                if parent:
                    parent.refresh_from_db()
                    src.get_ancestors().update(date=src.date)
                # обновление размера
                ancestors = src.get_ancestors(include_self=True).filter(type="FOLDER")
                if ancestors:
                    for ancestor in ancestors:
                        update_size(ancestor, date)
            step = 0
            request_list.remove(item)
    Item.objects.rebuild
    # записываем информацию об обновленных элементах
    updated_objects = Item.objects.filter(date=date)
    for item in updated_objects:
        stat_item = HistoryItem.objects.filter(itemId=item.id).filter(date=item.date)
        if not stat_item:
            data = {
                "id": item.id,
                "url": item.url,
                "parentId": item.parent_id,
                "type": item.type,
                "size": item.size,
                "date": item.date,
            }
            serializer = HistoryItemSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
    return Response(status=status.HTTP_200_OK)


@api_view(["GET"])
@throttle_classes([GetRequestsRateThrottle])
def item_nodes(request, item_pk):
    """
    Получение информации об элементе по идентификатору.
    """
    item = get_object_or_404(Item, id=item_pk)
    serializer = ItemSerializer(item)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["DELETE"])
@throttle_classes([PostDeleteRequestsRateThrottle])
def item_delete(request, item_pk):
    """
    Удаление элемента по идентификатору.
    """
    #проверим передан ли параметр date в запросе
    if not 'date' in request.query_params:
        raise ParseError("Отсутствует параметр date")
    if not request.query_params['date']:
        raise ParseError("Отсутствует параметр date")
    date = convert_str_to_datetime(request.GET['date'])
    if not date:
        raise ParseError("Неверный формат даты")

    item = get_object_or_404(Item, id=item_pk)

    # список родителей для обновления размера после удаления
    ancestors = item.get_ancestors(include_self=False).filter(type="FOLDER")

    # При удалении категории удаляются все дочерние элементы.
    node_items = item.get_descendants(include_self=True)
    # список id, которые будут удалены.
    id_to_del = []
    # по этому списку будут удаляться из HistoryItem
    for item in node_items:
        id_to_del.append(item.id)

    # удаляем элемент переданный в URL и его детей
    node_items.delete()
    # удаляем элементы из таблицы для статистики
    for item_id in id_to_del:
        items_to_delete = HistoryItem.objects.filter(itemId=item_id)
        if items_to_delete:
            items_to_delete.delete()
    # обновляем таблицу Item
    Item.objects.rebuild
    # обновление size родительских категорий
    if ancestors:
        for item in ancestors:
            update_size(item, date)

    return Response(status=status.HTTP_200_OK)


class ItemUpdates(generics.ListAPIView):
    """
    Получение списка файлов, которые были обновлены за последние 24 часа
    включительно [date - 24h, date] от времени переданном в запросе.
    """

    serializer_class = ItemSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = UpdatesFilter
    throttle_scope = "get_requests"

    def get_queryset(self):
        return Item.objects.all().filter(type="FILE")


class ItemHistory(generics.ListAPIView):
    """
    Получение истории обновлений по элементу за заданный полуинтервал [from, to).
    История по удаленным элементам недоступна.
    """

    serializer_class = HistoryItemSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = HistoryFilter
    throttle_scope = "get_requests"

    def get_queryset(self):
        queryset = HistoryItem.objects.filter(itemId=self.kwargs['item_pk'])
        if not queryset:
            raise Http404('Элемент не найден')
        return queryset



class ItemList(generics.ListAPIView):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
