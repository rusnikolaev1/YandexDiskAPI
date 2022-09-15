from rest_framework.views import exception_handler
from django.http import Http404
from rest_framework.exceptions import ValidationError
from http import HTTPStatus
from items.models import Item
from dateutil.parser import isoparse
import datetime


def update_size(obj: Item, date: datetime.datetime):
    """
    Обновление размера папок
    """
    if obj.type == "FILE":
        pass
    descendants = obj.get_descendants(include_self=False).filter(type="FILE")
    if not descendants:
        obj.size = 0
    if len(descendants) == 1:
        obj.size = descendants[0].size
    else:
        sum = 0
        for i in range(len(descendants)):
            if not descendants[i].size is None:
                sum += descendants[i].size

        obj.size = sum
        obj.date = date
    obj.save()


def convert_str_to_datetime(date_str: str):
    """
    Преобразует дату в формат ISO 8601
    """
    try:
        return isoparse(date_str)
    except:
        return None


def api_exception_handler(exc, context):
    #
    # Пользовательский обработчик API исключений.
    #
    # вызов стандартного обработчика ошибок
    # для получения деталей ошибки
    response = exception_handler(exc, context)

    if response is not None:
        http_code_to_message = {v.value: v.description for v in HTTPStatus}

        error_payload = {
            "code": 0,
            "message": "",
        }

        status_code = response.status_code
        error_payload["code"] = status_code
        if isinstance(exc, ValidationError):
            error_payload["message"] = "Validation Failed"
        elif isinstance(exc, Http404):
            error_payload["message"] = "Item not found"
        else:
            error_payload["message"] = http_code_to_message[status_code]
        response.data = error_payload
    return response
