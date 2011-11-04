

**EARLY WIP, PROBABLY TOTALLY BROKEN, DO NOT USE, ET CETERA, ET CETERA.**

# django-medusa

Allows rendering a Django-powered website into a static website a la *Jekyll*,
*Movable Type*, or other static page generation CMSes or frameworks.
**django-medusa** is designed to be as simple as possible and allow the
easy(ish) conversion of existing dynamic Django-powered websites -- nearly any
existing Django site installation (not relying on highly-dynamic content) can
be converted into a static generator which mirror's that site's output.

Given a "renderer" that defines a set of URLs (see below), this uses Django's
built-in `TestClient` to render out those views to either disk or Amazon S3.

At the moment, this likely does not scale to extremely large websites.

Optionally utilizes the `multiprocessing` library to speed up the rendering
process by rendering many views at once.

## Renderer classes

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
    AWS_STORAGE_BUCKET_NAME = ""

Be aware that the S3 renderer will overwrite any existing files that match
URL paths in your site.
