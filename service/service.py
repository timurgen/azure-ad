#!/usr/bin/env python3

import logging
import os
import json
from flask import Flask, Response, request as r

from str_utils import str_to_bool
from user_dao import sync_user_array, get_all_users
from group_dao import sync_group_array, get_all_groups
from dao_helper import init_dao, get_all_objects, init_dao_on_behalf_on
from logger_helper import log_request

env = os.environ.get

APP = Flask(__name__)
LOG_LEVEL = env('LOG_LEVEL', "INFO")
PORT = int(env('PORT', '5000'))
CT = 'application/json'

SUPPORTS_SINCE = str_to_bool(env('SUPPORTS_SINCE', 'false'))


@APP.route('/datasets/user/entities', methods=['GET'])
@log_request
def list_users():
    """
    Endpoint to fetch all users from Azure AD via MS graph API
    :request_argument since - delta token returned from last request (if exist)
    :return: JSON array with fetched users
    """
    init_dao(env('client_id'), env('client_secret'), env('tenant_id'))
    return Response(get_all_users(r.args.get('since')), content_type=CT)


@APP.route('/datasets/group/entities', methods=['GET'])
@log_request
def list_groups():
    """
    Endpoint to fetch all groups from Azure AD via MS graph API
    :request_argument since - delta token returned from last request (if exist)
    :return: JSON array with fetched groups
    """
    init_dao(env('client_id'), env('client_secret'), env('tenant_id'))
    return Response(get_all_groups(r.args.get('since')), content_type=CT)


@APP.route('/datasets/<path:kind>/entities', methods=['GET'])
@log_request
def list_objects(kind):
    """
    Endpoint to fetch all objects of given type from MS graph API
    :request_argument since - delta token returned from last request (if exist)
    :return: JSON array with fetched groups
    """
    if r.args.get('auth') and r.args.get('auth') == 'user':
        init_dao_on_behalf_on(env('client_id'), env('client_secret'), env('tenant_id'), env('username'),
                              env('password'))
    else:
        init_dao(env('client_id'), env('client_secret'), env('tenant_id'))
    return Response(
        get_all_objects(f'/{kind}/{"delta" if SUPPORTS_SINCE else ""}', r.args.get('since')),
        content_type=CT)


@APP.route('/datasets/user', methods=['POST'])
@log_request
def post_users():
    """
    Endpoint to synchronize users from Sesam into Azure AD
    :return: 200 empty response if everything OK
    """
    init_dao(env('client_id'), env('client_secret'), env('tenant_id'))
    sync_user_array(json.loads(r.data))
    return Response('')


@APP.route('/datasets/group', methods=['POST'])
@log_request
def post_groups():
    """
    Endpoint to synchronize groups from Sesam into Azure AD
    :return: 200 empty response if everything OK
    """
    init_dao(env('client_id'), env('client_secret'), env('tenant_id'))
    sync_group_array(json.loads(r.data))
    return Response('')


if __name__ == '__main__':
    """
    Application entry point
    """
    logging.basicConfig(level=logging.getLevelName(LOG_LEVEL))

    IS_DEBUG_ENABLED = True if logging.getLogger().isEnabledFor(logging.DEBUG) else False

    if IS_DEBUG_ENABLED:
        APP.run(debug=IS_DEBUG_ENABLED, host='0.0.0.0', port=PORT)
    else:
        import cherrypy

        cherrypy.tree.graft(APP, '/')
        cherrypy.config.update({
            'environment': 'production',
            'engine.autoreload_on': True,
            'log.screen': False,
            'server.socket_port': PORT,
            'server.socket_host': '0.0.0.0',
            'server.thread_pool': 10,
            'server.max_request_body_size': 0
        })

        cherrypy.engine.start()
        cherrypy.engine.block()
