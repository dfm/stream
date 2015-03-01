# -*- coding: utf-8 -*-

from __future__ import division, print_function

__all__ = [
    "IndexHandler", "CompletionHandler", "SoundcloudStreamHandler",
    "Application",
]

import os

import tornado.web
import tornado.gen
import tornado.httpclient
from tornado.options import options, define

from . import soundcloud


# Command line options.
define("port", default=3145, help="run on the given port", type=int)
define("debug", default=False, help="run in debug mode")
define("xheaders", default=True, help="use X-headers")
define("cookie_secret", default="secret key", help="secure key")


class IndexHandler(tornado.web.RequestHandler):

    def get(self):
        self.render("index.html")


class CompletionHandler(tornado.web.RequestHandler):

    @tornado.gen.coroutine
    def get(self):
        q = self.get_argument("q", None)
        if q is None or len(q) < 3:
            results = []
        else:
            params = dict(q=q, limit=5)
            response = yield soundcloud.request("/tracks", params=params)
            results = [dict(id=d["id"], title=d["title"],
                            user=d["user"]["username"],
                            artwork_url=d["artwork_url"])
                       for d in response if d["streamable"]]

        self.write(dict(count=len(results), results=results))
        self.finish()


class SoundcloudStreamHandler(tornado.web.RequestHandler):

    @tornado.gen.coroutine
    def get(self, id_):
        # Get the stream URL by not following redirects and catching the error.
        url = "/tracks/{0}/stream".format(id_)
        try:
            yield soundcloud.request(url, json=False, follow_redirects=False)
        except tornado.httpclient.HTTPError as error:
            # If a redirect was fired, the location will show up in the
            # headers.
            url = error.response.headers.get("Location", None)
            if url is not None:
                self.redirect(url)
                return

        # If we get here then the id was probably invalid.
        self.send_error(404)


class Application(tornado.web.Application):

    def __init__(self):
        handlers = [
            # Frontend views.
            (r"/", IndexHandler),

            # API views.
            (r"/complete", CompletionHandler),

            # Data access views.
            (r"/stream/soundcloud/([0-9]+)", SoundcloudStreamHandler),
        ]
        bp = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        settings = dict(
            template_path=os.path.join(bp, "templates"),
            static_path=os.path.join(bp, "static"),
            xsrf_cookies=True,
            xheaders=options.xheaders,
            cookie_secret=options.cookie_secret,
            debug=options.debug,
        )
        super(Application, self).__init__(handlers, **settings)
