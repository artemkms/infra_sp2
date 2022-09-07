from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

SLICE_REVIEW = 30


class User(AbstractUser):
    """
    Кастомная модель пользователя.
    Доп.поля: Био, Роль, Код подтверждения.
    Методы: is_moderator, is_admin
    """
    USER = 'user'
    MODERATOR = 'moderator'
    ADMIN = 'admin'

    USER_ROLES = (
        (USER, 'user'),
        (MODERATOR, 'moderator'),
        (ADMIN, 'admin')
    )
    bio = models.TextField(
        'Биография',
        blank=True,
    )
    role = models.CharField(
        'Роль',
        max_length=255,
        choices=USER_ROLES,
        default=USER,
        db_index=True
    )
    confirmation_code = models.TextField(
        'Код подтверждения',
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    @property
    def is_moderator(self):
        return self.role == User.MODERATOR

    @property
    def is_admin(self):
        return self.role == User.ADMIN or self.is_superuser

    def __str__(self):
        return str(self.username)


class Category(models.Model):
    """Модель для работы с категориями произведений"""
    name = models.CharField(
        max_length=256,
        verbose_name='Название категории'
    )
    slug = models.SlugField(
        unique=True,
        max_length=50,
        verbose_name='Slug категории',
    )

    class Meta:
        ordering = ('slug',)

    def __str__(self):
        return self.slug


class Genre(models.Model):
    """Модель для работы с жанрами произведений"""
    name = models.CharField(
        max_length=256,
        verbose_name='Название жанра'
    )
    slug = models.SlugField(
        unique=True,
        max_length=50,
        verbose_name='Slug жанра',
    )

    class Meta:
        ordering = ('slug',)

    def __str__(self):
        return self.slug


class Title(models.Model):
    """Модель для работы с произведениями"""
    name = models.CharField(
        max_length=256,
        verbose_name='Название произведения',
    )
    year = models.PositiveSmallIntegerField('Год выпуска')
    description = models.TextField('Описание', blank=True, null=True)
    genre = models.ManyToManyField(Genre, through='GenreTitle')
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='titles',
        verbose_name='Категория',
        help_text='Укажите категорию произведения'
    )

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name[:SLICE_REVIEW]


class GenreTitle(models.Model):
    """
    Вспомогательна модель для модели Titles, поля genre.
    Служит для реализации отношения many-to-many fields
    """
    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        related_name='genretitles',
    )
    genre = models.ForeignKey(
        Genre,
        on_delete=models.SET_NULL,
        null=True,
        related_name='genretitles',
    )

    class Meta:
        ordering = ('genre',)

    def __str__(self):
        return f'{self.title} {self.genre}'


class Review(models.Model):
    """Модель для работы с отзывами на произведения"""

    score = models.PositiveSmallIntegerField(
        default=None,
        validators=[
            MinValueValidator(1, 'минимальная оценка 1'),
            MaxValueValidator(10, 'максимальная оценка 10'),
        ]
    )
    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Отзывы',
        help_text='Отзыв на творческое произведение'
    )
    text = models.TextField(
        verbose_name='Текст отзыва',
        help_text='Расскажите что вы думаете об этом.'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Автор',
        help_text='Автор произведения',
    )
    pub_date = models.DateTimeField(
        'Дата отзыва',
        default=timezone.now,
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Отзыв',
        verbose_name_plural = 'Отзывы'

        indexes = [
            models.Index(fields=['author', 'title'], name='author_title'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'title'],
                name='unique_title'
            )
        ]

    def __str__(self):
        return self.text[:SLICE_REVIEW]


class Comment(models.Model):
    """Модель для работы с комментариями на отзывы"""
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    text = models.TextField(
        verbose_name='Текст комментария',
    )
    pub_date = models.DateTimeField(
        'Дата комментария',
        default=timezone.now,
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Комментарий'

    def __str__(self):
        return self.text[:SLICE_REVIEW]
