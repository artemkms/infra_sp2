"""
Модуль initdata используется для загрузки первоначальных данных моделей

    Основное применение - запускается из командной строки как
    managment команда.

    Имеет два режима запуска:

    -- без парамтров

    python manage.py initdata

    В данном режиме модуль пробует загрузить все модели указанные в словаре
    `ordered_load_models`. Подходит для загрузки в только что созданную базу.

    Note:
        Порядок загрузки имеет значение из за свяанных полей.
        Так модель Comment`, не может быть загружена впред `User`, в силу того
        что модель `Comment` имеет обязательное поле User, которое
        она не сможет получить в силу пустой таблицы `User`.

    -- с параметром --models

    python manage.py initdata --models User Genre Category

    В данном режиме модуль попроробует загрузить все модели перечисленные
    через пробел. Допускается указание одной модели.

    Note:
        Порядок загрузки определяет пользователь. Подходит для ручной
        перезагрузки моделей. Можно очистить руками таблицу базы данных и
        загрузить заново в нее данные по средствам команды описанной выше.

    Attributes
    ----------
    STATICFILES_DIRS : str
        какталог для статических файлов проекта
    MODELS_MODULE_NAME : str
        название модуля с моделями
    model_file_link : dict
        словарь связей модели с загружаемым файлом
        key : название модели
        val: название файла хранения данных

    model_fields_link: dict
        справочник для ручной связи полей модели с полем файла загрузки данных
        если связь не найдена, модуль пытается разрешить ее один в один.

    date_name_fields: list
        список имен полей в моделях, которые надо обрабатывать как поля даты
    ordered_load_models: tuple
        УпорядоченныйкКортеж с названиями моделей для загрузки, может быть
        расширен в случае появления дополнительных моделей в проект.

    Methods
    -------
    get_model(model_name)
        Получает модель по имени из коммандной строки или из кортежа

    get_model_csv_filename(name)
        получает имя файла для загрузки модели.

    create_kwargs(headers, row)
        получает заголовок csv файла с именами полей и текущую строку
        со значениями. Если заголовок поля файла это модель, то получает
        значение связанной модели, елси дата, то преобразует в формат
        datetime.datetime.

        Возвращает словарь, где ключи соответствуют названиям полей модели,
        а значения значениям для загрузки в модель.
"""

import csv
import datetime
import os.path

import pytz
from django.core.management.base import BaseCommand, CommandError

from api_yamdb.settings import STATICFILES_DIRS

MODELS_MODULE_NAME = 'reviews.models'

model_file_link = {
    'User': 'users',
    'Title': 'titles',
    'Comment': 'comments',
    'GenreTitle': 'genre_title'
}

model_fields_link = {
    'author': 'User',
}

date_name_fields = ['pub_date']

ordered_load_models = (
    'User', 'Category', 'Genre',
    'Title', 'GenreTitle', 'Review', 'Comment'
)


def get_model(model_name):
    """
    Получаем модель по имени из командной строки,
    либо из настроечной константы tuple: ordered_load_models
    """
    link_name = model_fields_link.get(model_name.lower())
    if link_name:
        model_name = link_name

    try:
        mod = __import__(MODELS_MODULE_NAME, fromlist=[model_name])
    except ImportError:
        print(f"Can't import model '{model_name}' from `{MODELS_MODULE_NAME}.")
        return None

    try:
        model = getattr(mod, model_name)
    except AttributeError:
        return None

    return model


def get_model_csv_filename(name):
    """
    Получаем файл csv с данными по имени модели.

    Для имен файлов не совпадающих с именами модели, используем ручную
    настройку через
    dict: model_file_link
    """
    link_name = model_file_link.get(name)
    if link_name:
        name = link_name

    csv_file = f'{name.lower()}.csv'
    file_path = f'{STATICFILES_DIRS[0]}data/{csv_file}'
    return file_path if os.path.isfile(file_path) else None


def create_kwargs(headers, row):
    """
    Создаем словарь из строки файла с параметрами загрузки.
    Ключи это поля модели. Значения это значения для установки в модель.

    """
    kwargs = {'id': headers[0]}

    for count, value in enumerate(row):
        title = headers[count]
        if title.endswith('_id'):
            title = title[:-3]

        model = get_model(title.capitalize())
        kwargs[title] = value

        if title in date_name_fields:
            frmt = "%Y-%m-%dT%H:%M:%S.%fZ"
            date = datetime.datetime.strptime(value, frmt)
            kwargs[title] = pytz.utc.localize(date)

        if model:
            try:
                kwargs[title] = model.objects.get(pk=int(value))
            except model.DoesNotExist:
                raise CommandError(
                    f'Related model `{title}` does not exist '
                    f'element id={value}'
                )

    return kwargs


class Command(BaseCommand):
    """Класс для работы с кастомными менеджмент коммандами"""
    help = 'Loads initial data for models'

    def add_arguments(self, parser):
        parser.add_argument('--models', nargs='+', type=str, default='--all')

    def handle(self, *args, **options):

        source = options['models']
        if options['models'] == '--all':
            source = ordered_load_models

        for name in source:
            model = get_model(name)
            file = get_model_csv_filename(name)
            if not all([model, file]):
                self.stdout.write(
                    self.style.ERROR(
                        f'Error loads model: `{name}` from file: {file}"'
                    )
                )
                continue

            with open(file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                headers = next(reader)
                for count, row in enumerate(reader):
                    kwargs = create_kwargs(headers, row)

                    try:
                        model.objects.update_or_create(
                            id=kwargs['id'], defaults=kwargs
                        )
                    except Exception:
                        raise CommandError('Can`t create model "%s"' % name)

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully load model `{name}`, '
                    f'create {count + 1} row in database.')
            )
