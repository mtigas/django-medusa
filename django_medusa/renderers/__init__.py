from django.conf import settings
from django.utils import importlib
from .base import BaseStaticSiteRenderer
from .disk import DiskStaticSiteRenderer
from .appengine import GAEStaticSiteRenderer
from .s3 import S3StaticSiteRenderer

__all__ = ('BaseStaticSiteRenderer', 'DiskStaticSiteRenderer',
           'S3StaticSiteRenderer', 'GAEStaticSiteRenderer',
           'StaticSiteRenderer')


def get_cls(renderer_name):
    mod_path, cls_name = renderer_name.rsplit('.', 1)
    mod = importlib.import_module(mod_path)
    return getattr(mod, cls_name)


DEFAULT_RENDERER = 'medusa.renderers.BaseStaticSiteRenderer'

# Define the default "django_medusa.renderers.StaticSiteRenderer" class as
# whatever class we have chosen in settings (defaulting to Base which will
# throw NotImplementedErrors when attempting to render).
StaticSiteRenderer = get_cls(getattr(settings,
    'MEDUSA_RENDERER_CLASS', DEFAULT_RENDERER
))
