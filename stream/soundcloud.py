# -*- coding: utf-8 -*-

from __future__ import division, print_function

__all__ = ["request"]

from tornado import gen
from tornado.httputil import url_concat
from tornado.httpclient import AsyncHTTPClient
from tornado.options import define, options
from tornado.escape import json_decode

define("soundcloud_id", default=None, help="the client id for soundcloud")

SOUNDCLOUD_URL = "https://api.soundcloud.com"


@gen.coroutine
def request(path=None, url=None, params=None, json=True, **kwargs):
    # Build the URL.
    if url is None:
        assert path is not None
        url = SOUNDCLOUD_URL + path

    # Determine the request arguments and append them to the URL.
    if params is None:
        params = dict()
    params["client_id"] = params.get("client_id", options.soundcloud_id)
    if params["client_id"] is None:
        raise ValueError("invalid soundcloud client id")
    url = url_concat(url, params)

    # Execute the request.
    response = yield AsyncHTTPClient().fetch(url, **kwargs)
    if json:
        raise gen.Return(json_decode(response.body))
    raise gen.Return(response)
