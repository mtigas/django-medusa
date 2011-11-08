from django.core.management.base import BaseCommand
from django_medusa.renderers import StaticSiteRenderer
from django_medusa.utils import get_static_renderers


class Command(BaseCommand):
    can_import_settings = True

    help = 'Looks for \'renderers.py\' in each INSTALLED_APP, which defines '\
           'a class for processing one or more URL paths into static files.'

    def handle(self, *args, **options):
        StaticSiteRenderer.initialize_output()

        for Renderer in get_static_renderers():
            r = Renderer()
            r.generate()

        StaticSiteRenderer.finalize_output()
