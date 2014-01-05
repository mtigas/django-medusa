from __future__ import print_function
from django.conf import settings
from django.test.client import Client
from .base import BaseStaticSiteRenderer
import os

__all__ = ('GAEStaticSiteRenderer', )

STANDARD_EXTENSIONS = (
    'htm', 'html', 'css', 'xml', 'json', 'js', 'yaml', 'txt'
)


# Unfortunately split out from the class at the moment to allow rendering with
# several processes via `multiprocessing`.
# TODO: re-implement within the class if possible?
def _gae_render_path(args):
    client, path, view = args
    if not client:
        client = Client()
    if path:
        DEPLOY_DIR = settings.MEDUSA_DEPLOY_DIR
        realpath = path
        if path.startswith("/"):
            realpath = realpath[1:]

        if path.endswith("/"):
            needs_ext = True
        else:
            needs_ext = False

        output_dir = os.path.abspath(os.path.join(
            DEPLOY_DIR,
            "deploy",
            os.path.dirname(realpath)
        ))
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        outpath = os.path.join(DEPLOY_DIR, "deploy", realpath)

        resp = client.get(path)
        if resp.status_code != 200:
            raise Exception

        mimetype = resp['Content-Type'].split(";", 1)[0]

        if needs_ext:
            outpath += "index.html"

        print(outpath)
        with open(outpath, 'w') as f:
            f.write(resp.content)

        rel_outpath = outpath.replace(
            os.path.abspath(DEPLOY_DIR) + "/",
            ""
        )
        if ((not needs_ext) and path.endswith(STANDARD_EXTENSIONS))\
        or (mimetype == "text/html"):
            # Either has obvious extension OR it's a regular HTML file.
            return None
        return "# req since this url does not end in an extension and also\n"\
               "# has non-html mime: %s\n"\
               "- url: %s\n"\
               "  static_files: %s\n"\
               "  upload: %s\n"\
               "  mime_type: %s\n\n" % (
                    mimetype, path, rel_outpath, rel_outpath, mimetype
               )


class GAEStaticSiteRenderer(BaseStaticSiteRenderer):
    """
    A variation of BaseStaticSiteRenderer that deploys directly to S3
    rather than to the local filesystem.

    Settings:
      * GAE_APP_ID
      * MEDUSA_DEPLOY_DIR
    """
    def render_path(self, path=None, view=None):
        return _gae_render_path((self.client, path, view))

    @classmethod
    def initialize_output(cls):
        print("Initializing output directory with `app.yaml`.")

        # Initialize the MEDUSA_DEPLOY_DIR with an `app.yaml` and `deploy`
        # directory which stores the static files on disk.
        DEPLOY_DIR = settings.MEDUSA_DEPLOY_DIR
        static_output_dir = os.path.abspath(os.path.join(
            DEPLOY_DIR,
            "deploy"
        ))
        app_yaml = os.path.abspath(os.path.join(
            DEPLOY_DIR,
            "app.yaml"
        ))
        if not os.path.exists(static_output_dir):
            os.makedirs(static_output_dir)

        # Initialize the app.yaml file
        app_yaml_f = open(app_yaml, 'w')
        app_yaml_f.write(
            "application: %s\n"\
            "version: 1\n"\
            "runtime: python\n"\
            "api_version: 1\n"\
            "threadsafe: true\n\n"\
            "handlers:\n\n" % settings.GAE_APP_ID
        )
        app_yaml_f.close()

    @classmethod
    def finalize_output(cls):
        print("Finalizing `app.yaml`.")

        DEPLOY_DIR = settings.MEDUSA_DEPLOY_DIR
        app_yaml = os.path.abspath(os.path.join(
            DEPLOY_DIR,
            "app.yaml"
        ))

        app_yaml_f = open(app_yaml, 'a')

        # Handle "root" index.html pages up to 10 paths deep.
        # This is pretty awful, but it's an easy way to handle arbitrary
        # paths and a) ensure GAE uploads all the files we want and b)
        # we don't encounter the 100 URL definition limit for app.yaml.
        app_yaml_f.write(
            "####################\n"\
            "# map index.html files to their root (up to 10 deep)\n"\
            "####################\n\n"
        )

        for num_bits in xrange(10):
            path_parts = "(.*)/" * num_bits
            counter_part = ""
            for c in xrange(0, num_bits):
                counter_part += "\\%s/" % (c + 1)

            app_yaml_f.write(
                "- url: /%s\n"\
                "  static_files: deploy/%sindex.html\n"\
                "  upload: deploy/%sindex.html\n\n" % (
                path_parts, counter_part, path_parts
            ))

        # Anything else not matched should just be uploaded as-is.
        app_yaml_f.write(
            "####################\n"\
            "# everything else\n"\
            "####################\n\n"\
            "- url: /\n"\
            "  static_dir: deploy"
        )
        app_yaml_f.close()

        print("You should now be able to deploy this to Google App Engine")
        print("by performing the following command:")
        print("appcfg.py update %s" % os.path.abspath(DEPLOY_DIR))

    def generate(self):
        DEPLOY_DIR = settings.MEDUSA_DEPLOY_DIR

        # Generate the site
        if getattr(settings, "MEDUSA_MULTITHREAD", False):
            # Upload up to ten items at once via `multiprocessing`.
            from multiprocessing import Pool

            print("Uploading with up to 10 upload processes...")
            pool = Pool(10)

            handlers = pool.map(
                _gae_render_path,
                ((None, path, None) for path in self.paths),
                chunksize=5
            )
            pool.close()
            pool.join()
        else:
            # Use standard, serial upload.
            self.client = Client()
            handlers = []
            for path in self.paths:
                handlers.append(self.render_path(path=path))

        DEPLOY_DIR = settings.MEDUSA_DEPLOY_DIR
        app_yaml = os.path.abspath(os.path.join(
            DEPLOY_DIR,
            "app.yaml"
        ))
        app_yaml_f = open(app_yaml, 'a')
        for handler_def in handlers:
            if handler_def is not None:
                app_yaml_f.write(handler_def)
        app_yaml_f.close()
