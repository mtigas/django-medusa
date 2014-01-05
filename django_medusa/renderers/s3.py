from __future__ import print_function
try:
    import cStringIO
except ImportError:  # >=Python 3.
    from io import StringIO as cStringIO
from datetime import timedelta, datetime
from django.conf import settings
from django.test.client import Client
from .base import BaseStaticSiteRenderer

__all__ = ('S3StaticSiteRenderer', )


def _get_cf():
    from boto.cloudfront import CloudFrontConnection
    return CloudFrontConnection(
        aws_access_key_id=settings.AWS_ACCESS_KEY,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    )


def _get_distribution():
    if not getattr(settings, "AWS_DISTRIBUTION_ID", None):
        return None

    conn = _get_cf()
    try:
        return conn.get_distribution_info(settings.AWS_DISTRIBUTION_ID)
    except:
        return None


def _get_bucket():
    from boto.s3.connection import S3Connection
    conn = S3Connection(
        aws_access_key_id=settings.AWS_ACCESS_KEY,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    )
    bucket = (settings.MEDUSA_AWS_STORAGE_BUCKET_NAME if settings.MEDUSA_AWS_STORAGE_BUCKET_NAME else settings.AWS_STORAGE_BUCKET_NAME)
    return conn.get_bucket(bucket)


def _upload_to_s3(key, file):
    key.set_contents_from_file(file, policy="public-read")

    cache_time = 0
    now = datetime.now()
    expire_dt = now + timedelta(seconds=cache_time * 1.5)
    if cache_time != 0:
        key.set_metadata('Cache-Control',
            'max-age=%d, must-revalidate' % int(cache_time))
        key.set_metadata('Expires',
            expire_dt.strftime("%a, %d %b %Y %H:%M:%S GMT"))
    key.make_public()


# Unfortunately split out from the class at the moment to allow rendering with
# several processes via `multiprocessing`.
# TODO: re-implement within the class if possible?
def _s3_render_path(args):
    client, bucket, path, view = args
    if not client:
        client = Client()

    if not bucket:
        bucket = _get_bucket()

    # Render the view
    resp = client.get(path)
    if resp.status_code != 200:
        raise Exception

    # Default to "index.html" as the upload path if we're in a dir listing.
    outpath = path
    if path.endswith("/"):
        outpath += "index.html"

    key = bucket.get_key(outpath) or bucket.new_key(outpath)
    key.content_type = resp['Content-Type']

    temp_file = cStringIO.StringIO(resp.content)
    md5 = key.compute_md5(temp_file)

    # If key is new, there's no etag yet
    if not key.etag:
        _upload_to_s3(key, temp_file)
        message = "Creating"

    else:
        etag = key.etag or ''
        # for some weird reason, etags are quoted, strip them
        etag = etag.strip('"').strip("'")
        if etag not in md5:
            _upload_to_s3(key, temp_file)
            message = "Updating"
        else:
            message = "Skipping"

    print("%s http://%s%s" % (
        message,
        bucket.get_website_endpoint(),
        path
    ))
    temp_file.close()
    return [path, outpath]


class S3StaticSiteRenderer(BaseStaticSiteRenderer):
    """
    A variation of BaseStaticSiteRenderer that deploys directly to S3
    rather than to the local filesystem.

    Requires `boto`.

    Uses some of the same settings as `django-storages`:
      * AWS_ACCESS_KEY
      * AWS_SECRET_ACCESS_KEY
      * AWS_STORAGE_BUCKET_NAME
    """
    @classmethod
    def initialize_output(cls):
        cls.all_generated_paths = []

    def render_path(self, path=None, view=None):
        return _s3_render_path((self.client, self.bucket, path, view))

    def generate(self):
        from boto.s3.connection import S3Connection

        self.conn = S3Connection(
            aws_access_key_id=settings.AWS_ACCESS_KEY,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        self.bucket = (self.conn.get_bucket(settings.MEDUSA_AWS_STORAGE_BUCKET_NAME) if settings.MEDUSA_AWS_STORAGE_BUCKET_NAME else self.conn.get_bucket(settings.AWS_STORAGE_BUCKET_NAME))
        self.bucket.configure_website("index.html", "500.html")
        self.server_root_path = self.bucket.get_website_endpoint()

        self.generated_paths = []
        if getattr(settings, "MEDUSA_MULTITHREAD", False):
            # Upload up to ten items at once via `multiprocessing`.
            from multiprocessing import Pool
            import itertools

            print("Uploading with up to 10 upload processes...")
            pool = Pool(10)

            path_tuples = pool.map(
                _s3_render_path,
                ((None, None, path, None) for path in self.paths),
                chunksize=5
            )
            pool.close()
            pool.join()

            self.generated_paths = list(itertools.chain(*path_tuples))
        else:
            # Use standard, serial upload.
            self.client = Client()
            for path in self.paths:
                self.generated_paths += self.render_path(path=path)

        type(self).all_generated_paths += self.generated_paths

    @classmethod
    def finalize_output(cls):
        dist = _get_distribution()
        if dist and dist.in_progress_invalidation_batches < 3:
            cf = _get_cf()
            req = cf.create_invalidation_request(
                settings.AWS_DISTRIBUTION_ID,
                cls.all_generated_paths
            )
            print(req.id)
