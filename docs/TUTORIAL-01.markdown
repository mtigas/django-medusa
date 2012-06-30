# Tutorial 1: The "hello world" of Django static websites

## Preliminaries

Set up a virtualenv, install Django and django-medusa, create a Django project
for this little website-ish thing:

    virtualenv my_medusa
    cd my_medusa
    echo "export PIP_RESPECT_VIRTUALENV=true" >> bin/activate
    echo "unset DJANGO_SETTINGS_MODULE" >> bin/activate
    source bin/activate

    pip install "django>=1.3,<1.5"
    pip install "https://github.com/mtigas/django-medusa/tarball/master#egg=django-medusa"

    django-admin.py startproject my_medusa_site
    cd my_medusa_site

## Configure your `settings.py`

In your favorite text editor, open `my_medusa_site/settings.py`.

Add the following to `INSTALLED_APPS`:

    'django_medusa',
    'my_medusa_site',

And then add this stuff to settings, too, preferrably near the bottom of
the file:

    # django_medusa -- disk-based renderer
    import os
    MEDUSA_RENDERER_CLASS = "django_medusa.renderers.DiskStaticSiteRenderer"
    PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
    MEDUSA_DEPLOY_DIR = os.path.join(
        PROJECT_DIR, '..', "_output"
    )

Create a `my_medusa_site/renderers.py` file (i.e., place `renderers.py` in the
directory alongside `settings.py` and `urls.py`), and make it contain:

    from django_medusa.renderers import StaticSiteRenderer

    class HomeRenderer(StaticSiteRenderer):
        def get_paths(self):
            return frozenset([
                "/",
            ])

    renderers = [HomeRenderer, ]

## Build you a static, Django-generated website

Now run the following (assuming you are in the same directory as `manage.py`)

    python manage.py staticsitegen

You should now see an `_output` directory show up next to your `manage.py`.
Inside it, you'll notice an `index.html` file that contains the contents
of the "It worked!" default Django page.

Congratulations, you've just rendered a Django website (sort of) to a static
website.

For more advanced topics (dynamically generating `renderer.get_paths` based
on models, rendering directly to S3, etc), see [the README][readme] and stay
tuned for future tutorials.

[readme]: https://github.com/mtigas/django-medusa/blob/master/README.markdown
