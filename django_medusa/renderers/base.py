__all__ = ['COMMON_MIME_MAPS', 'BaseStaticSiteRenderer']


# Since mimetypes.get_extension() gets the "first known" (alphabetically),
# we get supid behavior like "text/plain" mapping to ".bat". This list
# overrides some file types we will surely use, to eliminate a call to
# mimetypes.get_extension() except in unusual cases.
COMMON_MIME_MAPS = {
    "text/plain": ".txt",
    "text/html": ".html",
    "text/javascript": ".js",
    "application/javascript": ".js",
    "text/json": ".json",
    "application/json": ".json",
    "text/css": ".css",
}


class BaseStaticSiteRenderer(object):
    """
    This default renderer writes the given URLs (defined in get_paths())
    into static files on the filesystem by getting the view's response
    through the Django testclient.
    """

    def get_paths(self):
        """ Override this in a subclass to define the URLs to process """
        raise NotImplementedError

    @property
    def paths(self):
        """ Property that memoizes get_paths. """
        p = getattr(self, "_paths", None)
        if not p:
            p = self.get_paths()
            self._paths = p
        return p

    def render_path(self, path=None, view=None):
        raise NotImplementedError

    def generate(self):
        for path in self.paths:
            self.render_path(path)
