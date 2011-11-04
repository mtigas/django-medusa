from django.core.management.base import BaseCommand, CommandError
from django_medusa.utils import get_static_renderers

class Command(BaseCommand):
    can_import_settings = True

    help = 'Looks for \'renderers.py\' in each INSTALLED_APP, which defines '\
           'a class for processing one or more URL paths into static files.'

    def handle(self, *args, **options):
        for Renderer in get_static_renderers():
            r = Renderer()
            r.generate()

