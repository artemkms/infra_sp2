import datetime as dt

from django.db.models import Avg
from rest_framework import serializers, validators
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from reviews.models import (Category, Comment, Genre, GenreTitle, Review,
                            Title, User)


class CommentSerializer(serializers.ModelSerializer):
    """Сериализатор для упаковки комментариев."""
    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username'
    )

    class Meta:
        model = Comment
        fields = '__all__'
        read_only_fields = ('review', )


class ReviewSerializer(serializers.ModelSerializer):
    """Сериализатор для упаковки отзывов."""
    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username'
    )

    class Meta:
        model = Review
        fields = ('id', 'text', 'author', 'score', 'pub_date')


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор для упаковки категории"""

    class Meta:
        fields = ('name', 'slug')
        model = Category


class GenreSerializer(serializers.ModelSerializer):
    """Сериализатор для упаковки жанров"""

    class Meta:
        fields = ('name', 'slug')
        model = Genre


class TitleSerializer(serializers.ModelSerializer):
    """Сериализатор для упаковки произведений"""
    genre = GenreSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)
    rating = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'id', 'name', 'year', 'rating',
            'description', 'genre', 'category',
        )
        model = Title

    def get_rating(self, obj):
        """Получаем среднюю оценку произведения по оценкам пользователей"""
        rating = Review.objects.filter(
            title=obj.id
        ).aggregate(Avg('score'))['score__avg']
        if rating is not None:
            return round(rating)
        return None

    def validate_year(self, value):
        """Валидация года выпуска произведения, сравнивая с текущим годом"""
        now = dt.date.today().year
        if value >= now:
            raise serializers.ValidationError('Произведение еще не вышло')
        return value

    def validate(self, data):
        """Получаем первоначальные данные, переданные в поле `genre`
        и поле `category`, проводим их валидацию.
        """
        init_genre = self.initial_data.getlist('genre')
        if init_genre:

            if not(type(init_genre) == list):
                raise ValidationError(
                    f'`genre`: Invalid data format `{init_genre}`.'
                    f'Expected a list, but got `{type(init_genre)}`.'
                )

            for slug in init_genre:
                if not Genre.objects.filter(slug=slug).exists():
                    raise ValidationError(
                        f'`genre`: Does not exist slug str `{slug}`.'
                    )

            data['genre'] = init_genre

        init_category = self.initial_data.get('category')
        if not init_category:
            raise ValidationError(
                '`category`: This field is required.'
            )

        if not Category.objects.filter(slug=init_category).exists():
            raise ValidationError(
                f'`category`: Does not exist slug str `{init_category}.`'
            )

        data['category'] = Category.objects.get(slug=init_category)

        return data

    def create(self, validated_data):
        genres = validated_data.pop('genre')
        title, status = Title.objects.get_or_create(**validated_data)
        genre = Genre.objects.filter(slug__in=genres)
        title.genre.set(genre)

        return title

    def update(self, instance, validated_data):

        if validated_data.get('genre'):
            genres = validated_data.pop('genre')
            genre = Genre.objects.filter(slug__in=genres)
            instance.genre.set(genre)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance


class GenreTitles(serializers.ModelSerializer):

    class Meta:
        fields = ('title', 'genre')
        model = GenreTitle


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для работы с моделью User
    """
    username = serializers.RegexField(
        r'^[\w.@+-]+\Z',
        max_length=150,
        required=True,
        validators=[
            validators.UniqueValidator(
                queryset=User.objects.all(),
                message='Пользователь с таким именем уже существует.'
            )
        ]
    )
    email = serializers.EmailField(
        max_length=254,
        required=True,
        validators=[
            validators.UniqueValidator(
                queryset=User.objects.all(),
                message='Пользователь с таким email-адресом уже существует.'
            )
        ]
    )

    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'bio',
            'role'
        )
        lookup_field = 'username'


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания пользователя
    """
    username = serializers.RegexField(
        r'^[\w.@+-]+\Z',
        max_length=150,
        required=True,
    )
    email = serializers.EmailField(
        max_length=254,
        required=True,
    )

    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'bio',
            'role'
        )

    @staticmethod
    def validate_username(username):
        if username.lower() == 'me':
            raise serializers.ValidationError(
                {'username':
                 'Использовать имя "me" в качестве username запрещено.'}
            )
        return username

    def validate(self, attrs):
        """
        Валидация username и email.
        Если email и username совпадают, то все ок, делаем запрос на себя
        и получаем токен.
        Если совпадает только что-то одно, то выводим ошибку с инфой.
        """
        if User.objects.filter(username=attrs['username'],
                               email=attrs['email']).exists():
            return attrs
        if (
            User.objects.filter(username=attrs['username']).exists()
            or User.objects.filter(email=attrs['email']).exists()
        ):
            message_dict = {}
            if User.objects.filter(username=attrs['username']).exists():
                message_dict.update(
                    {
                        'username':
                        'Пользователь с именем {} уже есть в базе.'.format(
                            attrs['username']
                        )
                    }
                )
            if User.objects.filter(email=attrs['email']).exists():
                message_dict.update(
                    {
                        'email':
                        'Пользователь с адресом {} уже есть в базе.'.format(
                            attrs['email']
                        )
                    }
                )
            raise serializers.ValidationError(message_dict)
        return attrs


class ConfirmationSerializer(serializers.ModelSerializer):
    """
    Сериализатор для проверки конфирмейшн кода и выдачи токенов
    """
    username = serializers.CharField(max_length=150, required=True)
    confirmation_code = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = (
            'username',
            'confirmation_code'
        )

    def validate(self, attrs):
        user = get_object_or_404(User, username=attrs['username'])
        if not user.confirmation_code == attrs['confirmation_code']:
            raise serializers.ValidationError(
                {'confirmation_code': 'Неверный код подтверждения.'}
            )
        return attrs
