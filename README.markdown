# django-medusa

A super simple "static site generator" for Django sites. [Read more about this project here](https://mike.tig.as/blog/2012/06/30/django-medusa-rendering-django-sites-static-html/).

© 2011-2014 Mike Tigas. Licensed under the [MIT License](LICENSE).

---

**Note**: This project is largely unmaintained since 2014 and may be broken. If you
want to use something similar that's gotten more love lately, look at the following
which are still somewhat active, as of January 2016:

* [django-bakery](https://github.com/datadesk/django-bakery), built and maintained
  the lovely people at the [Los Angeles Times Data Desk](http://datadesk.latimes.com/).
  (Read about it [here](http://datadesk.latimes.com/posts/2012/03/introducing-django-bakery/).)
* [The alsoicode/django-medusa fork](https://github.com/alsoicode/django-medusa), by [Brandon Taylor](https://github.com/alsoicode). Among other things, it's been kept up to date for newer versions of Django.
* [django-freeze](https://github.com/fabiocaccamo/django-freeze) by [Fabio Caccamo](https://github.com/fabiocaccamo).
* [django-staticgen](https://github.com/mishbahr/django-staticgen) by [Mishbah Razzaque](https://github.com/mishbahr).

---

**django-medusa** allows rendering a Django-powered website into a static website a la *Jekyll*,
*Movable Type*, or other static page generation CMSes or frameworks.
It is designed to be as simple as possible and allow the
easy(ish) conversion of existing dynamic Django-powered websites -- nearly any
existing Django site installation (not relying on highly-dynamic content) can
be converted into a static generator which mirror's that site's output.

Given a "renderer" that defines a set of URLs (see below), this uses Django's
built-in `TestClient` to render out those views to either disk, Amazon S3,
or to Google App Engine.

At the moment, this likely does not scale to extremely large websites due to
the use of the internal `TestClient`. But django-medusa optionally uses the
`multiprocessing` library to speed up the rendering process by rendering many
views in parallel.

**For those uninterested in the nitty-gritty**, there are tutorials/examples
in the `docs` dir:

* [Tutorial 1: Hello World](https://github.com/mtigas/django-medusa/blob/master/docs/TUTORIAL-01.markdown)

## Renderer classes

Renderers live in `renderers.py` in each `INSTALLED_APP`.

Simply subclassing the `StaticSiteRenderer` class and defining `get_paths`
works:

    from django_medusa.renderers import StaticSiteRenderer

    class HomeRenderer(StaticSiteRenderer):
        def get_paths(self):
            return frozenset([
                "/",
                "/about/",
                "/sitemap.xml",
            ])

    renderers = [HomeRenderer, ]

A more complex example:

    from django_medusa.renderers import StaticSiteRenderer
    from myproject.blog.models import BlogPost


    class BlogPostsRenderer(StaticSiteRenderer):
        def get_paths(self):
            paths = ["/blog/", ]

            items = BlogPost.objects.filter(is_live=True).order_by('-pubdate')
            for item in items:
                paths.append(item.get_absolute_url())

            return paths

    renderers = [BlogPostsRenderer, ]

Or even:

    from django_medusa.renderers import StaticSiteRenderer
    from myproject.blog.models import BlogPost
    from django.core.urlresolvers import reverse


    class BlogPostsRenderer(StaticSiteRenderer):
        def get_paths(self):
            # A "set" so we can throw items in blindly and be guaranteed that
            # we don't end up with dupes.
            paths = set(["/blog/", ])

            items = BlogPost.objects.filter(is_live=True).order_by('-pubdate')
            for item in items:
                # BlogPost detail view
                paths.add(item.get_absolute_url())

                # The generic date-based list views.
                paths.add(reverse('blog:archive_day', args=(
                    item.pubdate.year, item.pubdate.month, item.pubdate.day
                )))
                paths.add(reverse('blog:archive_month', args=(
                    item.pubdate.year, item.pubdate.month
                )))
                paths.add(reverse('blog:archive_year', args=(item.pubdate.year,)))

            # Cast back to a list since that's what we're expecting.
            return list(paths)

    renderers = [BlogPostsRenderer, ]

## Renderer backends

### Disk-based static site renderer

Example settings:

    INSTALLED_APPS = (
        # ...
        # ...
        'django_medusa',
    )
    # ...
    MEDUSA_RENDERER_CLASS = "django_medusa.renderers.DiskStaticSiteRenderer"
    MEDUSA_MULTITHREAD = True
    MEDUSA_DEPLOY_DIR = os.path.abspath(os.path.join(
        REPO_DIR,
        'var',
        "html"
    ))

### S3-based site renderer

Example settings:

    INSTALLED_APPS = (
        # ...
        # ...
        'django_medusa',
    )
    # ...
    MEDUSA_RENDERER_CLASS = "django_medusa.renderers.S3StaticSiteRenderer"
    MEDUSA_MULTITHREAD = True
    AWS_ACCESS_KEY = ""
    AWS_SECRET_ACCESS_KEY = ""
    MEDUSA_AWS_STORAGE_BUCKET_NAME = "" # (also accepts AWS_STORAGE_BUCKET_NAME)

Be aware that the S3 renderer will overwrite any existing files that match
URL paths in your site.

The S3 backend will force "index.html" to be the Default Root Object for each
directory, so that "/about/" would actually be uploaded as "/about/index.html",
but properly loaded by the browser at the "/about/" URL.

**BONUS:** Additionally, the S3 renderer keeps the "Content-Type" HTTP header
that the view returns: if "/foo/json/" returns a JSON file (application/json),
the file will be uploaded to "/foo/json/index.html" but will be served as
application/json in the browser -- and will be accessible from "/foo/json/".

### App Engine-based site renderer

Example settings:

    INSTALLED_APPS = (
        # ...
        # ...
        'django_medusa',
    )
    # ...
    MEDUSA_RENDERER_CLASS = "django_medusa.renderers.GAEStaticSiteRenderer"
    MEDUSA_MULTITHREAD = True
    MEDUSA_DEPLOY_DIR = os.path.abspath(os.path.join(
        REPO_DIR,
        'var',
        "html"
    ))
    GAE_APP_ID = ""

This generates a `app.yaml` file and a `deploy` directory in your
`MEDUSA_DEPLOY_DIR`. The `app.yaml` file contains the URL mappings to upload
the entire site as a static files.

App Engine generally follows filename extensions as the mimetype. If you have
paths that don't have an extension and are *not* HTML files (i.e.
"/foo/json/", "/feeds/blog/", etc.), the mimetype from the "Content-Type" HTTP
header will be manually defined for this URL in the `app.yaml` path.

## Usage

1. Install `django-medusa` into your python path (TODO: setup.py) and add
   `django_medusa` to `INSTALLED_APPS`.
2. Select a renderer backend (currently: disk or s3) in your settings.
2. Create renderer classes in `renderers.py` under the apps you want to render.
3. `django-admin.py staticsitegen`
4. ???
5. Profit!

#### Example

From the first example in the "**Renderer classes**" section, using the
disk-based backend.

    $ django-admin.py staticsitegen
    Found renderers for 'myproject'...
    Skipping app 'django.contrib.syndication'... (No 'renderers.py')
    Skipping app 'django.contrib.sitemaps'... (No 'renderers.py')
    Skipping app 'typogrify'... (No 'renderers.py')

    Generating with up to 8 processes...
    /project_dir/var/html/index.html
    /project_dir/var/html/about/index.html
    /project_dir/var/html/sitemap.xml
