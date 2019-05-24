import logging
import requests
import json
import os
from auth_helper import get_token
from urllib.parse import urlparse, parse_qs

GRAPH_URL = 'https://graph.microsoft.com/v1.0'

ALLOWED_METHODS = ['get', 'post', 'put', 'patch']

METADATA = os.environ.get('odata_metadata', 'minimal')

__token = None


def init_dao(client_id, client_secret, tenant_id):
    global __token
    __token = get_token(client_id, client_secret, tenant_id)


def make_request(url, method, data=None):
    """
    Function to send request to given URL with given method using given token
    :param url: where to send request
    :param method: which method to use. An exception will be thrown if method is not allowed
    :param data: request payload for POST/PUT/PATCH requests
    :return: decoded JSON object
    """
    if method.lower() not in ALLOWED_METHODS:
        raise Exception(f'Method {method} is not allowed')

    t_type = __token['token_type']
    t_value = __token['access_token']

    headers = {
        'Authorization': f'{t_type} {t_value}',
        "Accept": f'application/json;odata.metadata={METADATA};odata.streaming=true'
    }

    if method != 'GET':
        headers['Content-Type'] = 'application/json'

    call_method = getattr(requests, method.lower())
    api_call_response = call_method(url, headers=headers, verify=True, json=data)

    try:
        api_call_response.raise_for_status()
    except requests.exceptions.HTTPError as error:
        logging.error(error)
        logging.error(error.response.text)
        raise Exception from error

    return json.loads(api_call_response.text) if len(api_call_response.text) > 0 else {}


def get_all_objects(resource_path, delta=None):
    """
    Fetch and stream back objects from MS Graph API
    :param resource_path path to needed resource in MS Graph API
    :param delta: delta token from last request.
    More about delta https://docs.microsoft.com/en-us/graph/delta-query-users
    :return: generate JSON output with all fetched users
    """
    first = True
    url = GRAPH_URL + resource_path

    if delta:
        url += f'?$deltatoken={delta}'

    yield '['

    while url is not None:
        result = make_request(url, 'get')

        if result.get('@odata.deltaLink'):
            parsed_url = urlparse(result.get('@odata.deltaLink'))
            query = parse_qs(parsed_url.query)
            delta = query['$deltatoken'][0]

        for item in result['value']:
            if not first:
                yield ','
            else:
                first = False

            item['_updated'] = delta
            item['_id'] = item['id']

            yield json.dumps(item)

        url = result.get('@odata.nextLink', None)

    yield ']'
