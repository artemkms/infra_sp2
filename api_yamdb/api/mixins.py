from rest_framework.mixins import (CreateModelMixin, DestroyModelMixin,
                                   ListModelMixin)
from rest_framework.viewsets import GenericViewSet

from .permissions import AdminOrReadonly


class CreateListDeleteMixinSet(
        ListModelMixin,
        CreateModelMixin,
        DestroyModelMixin,
        GenericViewSet):
    """
    Миксин для вюсетов: методы GET (только список), POST и DELETE.
    GET - разрешён всем.
    POST, DELETE - только администраторам.
    """
    permission_classes = (AdminOrReadonly, )
