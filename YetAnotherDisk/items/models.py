from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
from collections import defaultdict


# список возможных типов
TYPE_CHOICES = (
    ("FILE", "FILE"),
    ("FOLDER", "FOLDER"),
)


class Item(MPTTModel):
    """
    Модель хранения информации о файлах и папках
    """

    id = models.TextField(
        primary_key=True,
        verbose_name="Уникальный идентфикатор",
        unique=True,
        null=False,
    )
    url = models.CharField(
        max_length=255,
        verbose_name="Ссылка на файл. Для папок поле равнно null.",
        null=True,
    )
    parent = TreeForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        related_name="children",
        verbose_name="Уникальный идентфикатор родительской категории",
    )
    type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        verbose_name="Тип элемента - папка или файл",
        null=False,
    )
    size = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Целое число, для папки - это суммарный размер всех элеметов.",
    )
    date = models.DateTimeField(verbose_name="Дата и время обновления", null=False)


class HistoryItem(models.Model):
    """
    Хранение исторической информации о товарах и категориях
    """

    itemId = models.TextField()
    url = models.CharField(
        max_length=255,
        null=True,
    )
    parentId = models.TextField(
        null=True,
    )
    type = models.CharField(
        max_length=10,
        null=False,
    )
    size = models.IntegerField(null=True)
    date = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["date", "itemId"], name="unique_update")
        ]
        ordering = ("-date",)
