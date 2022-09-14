from django_filters import rest_framework as filters
from items.models import Item, HistoryItem
import datetime
from rest_framework.exceptions import ParseError


class UpdatesFilter(filters.FilterSet):
    """
    Получение списка файлов, которые были обновлены за последние 24 часа
    включительно [date - 24h, date] от времени переданном в запросе.
    """

    date = filters.DateTimeFilter(field_name="date", method="prev24hours")

    class Meta:
        model = Item
        fields = ("date",)

    def prev24hours(
        self,
        queryset,
        field_name,
        value,
    ):
        if value:

            return queryset.filter(date__gte=value - datetime.timedelta(days=1)).filter(
                date__lte=value
            )


class HistoryFilter(filters.FilterSet):
    """
    Получение истории обновлений по элементу за заданный полуинтервал [from, to).
    История по удаленным элементам недоступна.
    """

    dateStart = filters.DateTimeFilter(field_name="date", lookup_expr="gte")
    dateEnd = filters.DateTimeFilter(field_name="date", lookup_expr="lt")

    class Meta:
        model = HistoryItem
        fields = ("dateStart", "dateEnd")
