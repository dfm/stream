#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, print_function

import os
import time

import tornado.web
import tornado.ioloop
import tornado.websocket
import tornado.httpserver
from tornado.httpclient import HTTPError
from tornado import gen
from tornado.escape import json_decode, json_encode
from tornado.options import define, options, parse_command_line

from stream import soundcloud

define("port", default=3145, help="run on the given port", type=int)
define("debug", default=False, help="run in debug mode")
define("xheaders", default=True, help="use X-headers")
define("cookie_secret", default="secret key", help="secure key")


class Application(tornado.web.Application):

    def __init__(self):
        handlers = [
            (r"/", IndexHandler),
            (r"/complete", CompleteHandler),
            (r"/socket", SocketHandler),
            (r"/stream/([0-9]+)", StreamHandler),
        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=True,
            xheaders=options.xheaders,
            cookie_secret=options.cookie_secret,
            debug=options.debug,
        )
        super(Application, self).__init__(handlers, **settings)


class IndexHandler(tornado.web.RequestHandler):

    def get(self):
        self.render("index.html")


class CompleteHandler(tornado.web.RequestHandler):

    @gen.coroutine
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


class StreamHandler(tornado.web.RequestHandler):

    @gen.coroutine
    def get(self, id_):
        # Get the stream URL by not following redirects and catching the error.
        url = "/tracks/{0}/stream".format(id_)
        try:
            yield soundcloud.request(url, json=False, follow_redirects=False)
        except HTTPError as error:
            # If a redirect was fired, the location will show up in the
            # headers.
            url = error.response.headers.get("Location", None)
            if url is not None:
                self.redirect(url)
                return

        # If we get here then the id was probably invalid.
        self.send_error(404)


class SocketHandler(tornado.websocket.WebSocketHandler):

    clients = set()
    start_time = time.time()

    def get_compression_options(self):
        # Non-None enables compression with default options.
        return {}

    def open(self):
        SocketHandler.clients.add(self)

    def on_close(self):
        SocketHandler.clients.remove(self)

    def on_message(self, event):
        message = json_decode(event)
        message_type = message.get("t", None)
        if message_type is None:
            return

        # Pass updates directly through to the clients.
        if message_type == "update":
            for client in SocketHandler.clients:
                if client == self:
                    continue
                client.write_message(event)

        # Get the current time.
        self.write_message(json_encode({
            "time": time.time(),
            "strt": SocketHandler.start_time,
        }))


def main():
    parse_command_line()

    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port, address="127.0.0.1")
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
