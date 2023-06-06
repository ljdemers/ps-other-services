from urllib.parse import urlparse, urlunparse

from werkzeug.urls import url_decode, url_encode
from flask.json import dumps
from flask.globals import current_app
from flask.wrappers import Response


class HTTPResponse(Response):
    pass


def csv(data, filename, status=200, headers=None,
        content_type="text/csv", mimetype="text/csv"):
    """
    Returns response object with body in json format.
    :param data: Response data to be sent.
    :param filename: Response file name.
    :param status: Response code.
    :param headers: Custom Headers.
    """
    all_headers = {
        "Content-Disposition": "attachment; filename={0}".format(filename),
        "Content-Type": content_type,
    }
    if headers is not None:
        all_headers.update(headers)
    return current_app.response_class(
        data, headers=all_headers, status=status, content_type=content_type,
        mimetype=mimetype,
    )


def json(body, status=200, headers=None,
         content_type="application/json", **kwargs):
    """
    Returns response object with body in json format.
    :param body: Response data to be serialized.
    :param status: Response code.
    :param headers: Custom Headers.
    :param kwargs: Remaining arguments that are passed to the json encoder.
    """
    data = dumps(body, **kwargs)
    return current_app.response_class(
        data, headers=headers, status=status, content_type=content_type,
        mimetype=current_app.config['JSONIFY_MIMETYPE'],
    )


def rebuild_page_url(url, page_num):
    url_obj = urlparse(url)
    url_qs = url_decode(url_obj.query)
    url_qs['page'] = page_num
    new_query = url_encode(url_qs)
    return urlunparse((
        url_obj.scheme, url_obj.netloc, url_obj.path, url_obj.params,
        new_query, url_obj.fragment,
    ))


def json_page(request, page, **json_kwargs):
    meta = {
        "count": page.paginator.count,
    }

    links = {}
    if page.paginator.num_pages:
        links["first"] = rebuild_page_url(request.url, 1)
        links["last"] = rebuild_page_url(request.url, page.paginator.num_pages)
    if page.has_previous():
        prev_page_num = page.previous_page_number()
        links['prev'] = rebuild_page_url(request.url, prev_page_num)
    if page.has_next():
        next_page_num = page.next_page_number()
        links['next'] = rebuild_page_url(request.url, next_page_num)

    body = {
        "data": page.items,
        "meta": meta,
        "links": links,
    }
    return json(body, **json_kwargs)
