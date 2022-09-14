from django.urls import path, include
from rest_framework.authtoken import views
from api.views import (
    item_imports,
    item_nodes,
    item_delete,
    ItemUpdates,
    ItemHistory,
    ItemList,
)


app_name = "api"

urlpatterns = [
    path("", ItemList.as_view()),
    path("imports", item_imports),
    path("nodes/<str:item_pk>", item_nodes),
    path("delete/<str:item_pk>", item_delete),
    path("updates", ItemUpdates.as_view()),
    path("node/<str:item_pk>/history", ItemHistory.as_view()),
]
