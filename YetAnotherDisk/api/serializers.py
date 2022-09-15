from rest_framework import serializers
from items.models import Item, HistoryItem


class ItemSerializer(serializers.ModelSerializer):
    parentId = serializers.CharField(
        source="parent_id", allow_null=True, required=False
    )
    url = serializers.CharField(allow_null=True, required=False)
    size = serializers.IntegerField(allow_null=True, required=False)
    children = serializers.SerializerMethodField()
    date = serializers.DateTimeField()

    class Meta:
        model = Item
        fields = (
            "id",
            "url",
            "type",
            "parentId",
            "date",
            "size",
            "children",
        )

    def get_children(self, obj):
        children = ItemSerializer(obj.get_children(), many=True).data
        if not children:
            return None
        return children

    def validate(self, data):
        if "parent_id" in data.keys():
            if not data["parent_id"]:
                parent = None
            else:
                parent = Item.objects.filter(id=data["parent_id"]).first()
                if parent:
                    if parent.type != "FOLDER":
                        raise serializers.ValidationError(
                            "У родителя тип должен быть FOLDER"
                        )
                else:
                    # если указан несуществующий родитель
                    raise serializers.ValidationError("Указан несуществующий родитель")
        else:
            parent = None

        if "size" in data.keys():
            # у папок поле size должно содержать null
            if (data["type"] == "FOLDER") and data["size"]:
                raise serializers.ValidationError(
                    "У типов FOLDER поле size должно быть null"
                )
            # у файлов поле size должно быть больше 0
            if data["type"] == "FILE":
                if not data["size"]:
                    raise serializers.ValidationError(
                        "У типов FILE поле size должно быть заполнено"
                    )
                else:
                    if data["size"] < 0:
                        raise serializers.ValidationError(
                            "У типов FILE поле size должно быть больше 0"
                        )
        else:
            # у файлов поле size не может быть не заполнено
            if data["type"] == "FILE":
                raise serializers.ValidationError("У типов FILE должно быть поле size")

        if "url" in data.keys():
            if (data["type"] == "FOLDER") and data["url"]:
                # поле url при импорте папки всегда должно быть равно null
                raise serializers.ValidationError(
                    "У типов FOLDER поле url должно быть null"
                )
            if data["type"] == "FILE":
                if not data["url"]:
                    raise serializers.ValidationError(
                        "У типов FILE поле url должно быть заполнено"
                    )
                else:
                    if len(data["url"]) > 255:
                        raise serializers.ValidationError(
                            "Поле url должно быть не более 255"
                        )
        else:
            # если url нет и тип File, то ошибка
            if data["type"] == "FILE":
                raise serializers.ValidationError("У типов FILE должно быть поле url")

        # найдем этот объект среди существующих
        item = Item.objects.filter(id=data["id"]).first()
        if item:
            # тип объекта должен быть прежним
            if item.type != data["type"]:
                raise serializers.ValidationError(
                    "Изменение типа элемента с папки на файл и с файла на папку не допускается."
                )
            # поле date у Item в БД должно быть строго меньше чем data['date']
            if item.date >= data["date"]:
                raise serializers.ValidationError(
                    "Поле updateDate должно монотонно возрастать"
                )
        return data

    def create(self, validated_data):
        validated_data["parent"] = Item.objects.filter(
            id=validated_data.get("parent_id")
        ).first()
        return Item.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.size = validated_data.get("size", instance.size)
        instance.date = validated_data.get("date", instance.date)
        instance.parent = Item.objects.filter(
            id=validated_data.get("parent_id")
        ).first()
        instance.url = validated_data.get("url", instance.url)
        instance.save()
        return instance


class HistoryItemSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="itemId")
    url = serializers.CharField(allow_null=True, required=False)
    parentId = serializers.CharField(
        allow_null=True,
    )
    size = serializers.IntegerField(
        allow_null=True,
    )
    date = serializers.DateTimeField()

    class Meta:
        model = HistoryItem
        fields = (
            "id",
            "url",
            "date",
            "parentId",
            "size",
            "type",
        )


class SingleItemSerializer(serializers.ModelSerializer):
    parentId = serializers.CharField(
        source="parent_id", allow_null=True, required=False
    )

    class Meta:
        model = Item
        fields = (
            "id",
            "url",
            "date",
            "parentId",
            "size",
            "type",
        )
