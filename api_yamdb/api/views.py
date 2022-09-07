from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from reviews.models import Category, Genre, Review, Title, User

from .filters import TitleFilter
from .mixins import CreateListDeleteMixinSet
from .permissions import (AdminOnlyPermission, AdminOrReadonly,
                          AuthorModeratorAdminOrReadOnly)
from .serializers import (CategorySerializer, CommentSerializer,
                          ConfirmationSerializer, GenreSerializer,
                          ReviewSerializer, TitleSerializer,
                          UserCreateSerializer, UserSerializer)


class CategoryViewSet(CreateListDeleteMixinSet):
    """Вью сет для работы с категориями произведений"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (AdminOrReadonly, )
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'


class GenreViewSet(CreateListDeleteMixinSet):
    """Вью сет для работы с жанрами произведений"""
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = (AdminOrReadonly, )
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'


class TitleViewSet(viewsets.ModelViewSet):
    """Вью сет для работы с произведениями"""
    queryset = Title.objects.all()
    serializer_class = TitleSerializer
    filter_backends = (DjangoFilterBackend, )
    filterset_class = TitleFilter
    permission_classes = (AdminOrReadonly, )


class CommentViewSet(viewsets.ModelViewSet):
    """Вью сет для работы с комментариями к произведениям."""
    serializer_class = CommentSerializer
    permission_classes = (AuthorModeratorAdminOrReadOnly, )

    def get_queryset(self):
        review_id = self.kwargs.get('review_id')
        review = get_object_or_404(Review, pk=review_id)
        return review.comments.all()

    def perform_create(self, serializer):
        review_id = self.kwargs.get('review_id')
        review = get_object_or_404(Review, pk=review_id)
        serializer.save(review=review, author=self.request.user)


class ReviewViewSet(viewsets.ModelViewSet):
    """Вью сет для работы с отзывами на произведения"""
    serializer_class = ReviewSerializer
    permission_classes = (AuthorModeratorAdminOrReadOnly, )

    def get_queryset(self):
        title_id = self.kwargs.get('title_id')
        title = get_object_or_404(Title, pk=title_id)
        return title.reviews.all()

    def perform_create(self, serializer):
        title_id = self.kwargs.get('title_id')
        if self.request.user.reviews.filter(title=title_id).exists():
            raise ValidationError("Only one reviews in titles, sorry.")

        title = get_object_or_404(Title, pk=title_id)
        serializer.save(author=self.request.user, title=title)


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет для модели User"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (AdminOnlyPermission, )
    lookup_field = 'username'

    @action(
        methods=['get', 'patch'],
        detail=False,
        permission_classes=[permissions.IsAuthenticated, ]
    )
    def me(self, request):
        """
        Функция редактирования профайла.
        Показывает учетные данные авторизованного пользователя.
        Дает возможность их отредактировать.
        """
        if request.method.lower() == 'get':
            serializer = UserSerializer(instance=request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        serializer = UserSerializer(request.user,
                                    data=request.data,
                                    partial=True)
        if serializer.is_valid():
            if (
                'role' in serializer.validated_data
                and not request.user.is_admin
            ):
                serializer.validated_data['role'] = request.user.role
            serializer.save()
            return Response(serializer.validated_data,
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserCreateAPIView(APIView):
    """
    Класс для создания нового пользователя
    """
    def post(self, request, *args, **kwargs):
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            if not User.objects.filter(
                username=serializer.validated_data['username']
            ).exists():
                serializer.save(role='user')
            user = User.objects.get(
                username=serializer.validated_data['username']
            )
            user.confirmation_code = str(RefreshToken.for_user(user))
            user.save(update_fields=['confirmation_code'])
            send_mail(
                'Confirmation code.',
                user.confirmation_code,
                'no_replay@yambd.ru',
                [user.email, ],
                fail_silently=False,
            )
            return Response(
                serializer.validated_data,
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ConfirmationAPIView(APIView):
    """
    Класс для получения токена по коду подтверждения `confirmation_code`.
    """
    def post(self, request, *args, **kwargs):
        serializer = ConfirmationSerializer(data=request.data)
        if serializer.is_valid():
            user = User.objects.get(
                username=serializer.validated_data['username']
            )
            user.confirmation_code = ''
            user.save(update_fields=['confirmation_code'])
            return Response(
                {'token': str(RefreshToken.for_user(user).access_token)},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
