
import collections
import logging
import os

appdir = os.path.dirname(__file__)

import lib

from jinja2 import BaseLoader, Environment, TemplateNotFound
from werkzeug.wrappers import Request, Response
from werkzeug.middleware.shared_data import SharedDataMiddleware


Page = collections.namedtuple('Page', ['path', 'file', 'name', 'title'])

pages = [
    Page(path='/',        file='home',    name='Home',    title="Mikel's Home Page"),
    Page(path='/about',   file='about',   name='About',   title="About Mikel"),
    Page(path='/contact', file='contact', name='Contact', title="Contact Mikel"),
    Page(path='/resume',  file='resume',  name='Resume',  title="Mikel's Resume"),
]

notfound = Page(path='', file='notfound', name='Not Found', title="Page Not Found")

sitemap = {
    page.path: page
    for page in pages
}


class FileLoader(BaseLoader):
    """Template loader that uses an on-disk path matching the template path."""

    def __init__(self, path):
        self.path = path

    def get_source(self, environment, template):
        path = os.path.join(self.path, template)
        if not os.path.exists(path):
            raise TemplateNotFound(template)
        mtime = os.path.getmtime(path)
        with open(path) as f:
            source = f.read()
        return source, path, lambda: mtime == os.path.getmtime(path)


templatedir = os.path.join(appdir, 'templates')
env = Environment(loader=FileLoader(templatedir))


@Request.application
def templateapp(request):
    try:
        logging.info('Request for %s', request.url)
        template = env.get_template('app.jinja')
        path = normalize_path(request.path)
        page, status = sitemap.get(path), 200
        if not page:
            logging.info('No page for %s', path)
            page, status = notfound, 404
        menu_items = menu_items_for_path(path)
        return Response(template.render(name=page.name, path=page.path,
                                        file=page.file, title=page.title,
                                        menu_items=menu_items),
                        content_type='text/html; charset=utf-8',
                        status=status)
    except Exception as e:
        logging.error('Error handling request for %s: %s', request.path, e)
        return Response('Error generating page', status=500)


app = SharedDataMiddleware(templateapp, {
    '/static': os.path.join(os.path.dirname(__file__), 'static'),
    '/styles': os.path.join(os.path.dirname(__file__), 'styles'),
})


def normalize_path(path):
    if path.endswith('.html'):
        path = path[:-5]
    path = path.rstrip('/')
    if not path:
        path = '/'
    return path


def menu_items_for_path(path):
    for url in sorted(sitemap):
        page = sitemap[url]
        yield (page.name, page.path)


#  vim: set ts=8 sw=4 tw=0 et:
