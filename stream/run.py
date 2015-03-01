# -*- coding: utf-8 -*-

from __future__ import division, print_function

__all__ = ["run_application"]

import tornado.ioloop
import tornado.httpserver
from tornado.options import options, parse_command_line

from .server import Application


def run_application():
    parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port, address="127.0.0.1")
    tornado.ioloop.IOLoop.instance().start()
