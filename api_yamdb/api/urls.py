from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import (CategoryViewSet, CommentViewSet, ConfirmationAPIView,
                    GenreViewSet, ReviewViewSet, TitleViewSet,
                    UserCreateAPIView, UserViewSet)

app_name = 'api'

v1_router = SimpleRouter()
v1_router.register('users', UserViewSet)
v1_router.register('categories', CategoryViewSet, basename='categories')
v1_router.register('genres', GenreViewSet, basename='genres')
v1_router.register('titles', TitleViewSet, basename='titles')
v1_router.register(
    r"titles/(?P<title_id>[^/.]+)/reviews", ReviewViewSet, basename='reviews'
)
v1_router.register(
    r"titles/(?P<title_id>[^/.]+)/reviews/(?P<review_id>[^/.]+)/comments",
    CommentViewSet,
    basename='comment'
)

urlpatterns = [
    path('v1/auth/signup/', UserCreateAPIView.as_view(), name='user_create'),
    path('v1/auth/token/', ConfirmationAPIView.as_view(), name='confirm_user'),
    path('v1/', include(v1_router.urls)),
]
