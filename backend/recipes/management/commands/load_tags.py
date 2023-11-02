import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from recipes.models import Tag

FILE_NOT_FOUND = 'Не найден json файл в директории {}'
SUCCESS = 'Данные добавлены в базу'


class Command(BaseCommand):

    def handle(self, *args, **options):
        file_path = os.path.join(settings.CSVDATA_ROOT, 'tags.json')
        if not os.path.isfile(file_path):
            raise CommandError(FILE_NOT_FOUND.format(file_path))
        with open(file_path, 'r', encoding='utf-8') as data:
            reader = json.load(data)
            Tag.objects.bulk_create(
                (Tag(
                    name=item['name'],
                    color=item['color'], slug=item['slug'])
                    for item in reader),
                ignore_conflicts=True)
        self.stdout.write(SUCCESS)
