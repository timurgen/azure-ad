import logging
import os
import json
from flask import Flask, Response, request as r
from user_dao import sync_user_array
from group_dao import sync_group_array
from dao_helper import init_dao, get_all_objects
from logger_helper import log_request

APP = Flask(__name__)
LOG_LEVEL = os.environ.get('LOG_LEVEL', "INFO")
PORT = int(os.environ.get('PORT', '5000'))
CT = 'application/json'
env = os.environ.get


@APP.route('/datasets/<kind>/entities', methods=['GET'])
@log_request
def list_objects(kind):
    """
    Endpoint to fetch all objects of given type from MS graph API
    :request_argument since - delta token returned from last request (if exist)
    :return: JSON array with fetched groups
    """
    init_dao(env('client_id'), env('client_secret'), env('tenant_id'))
    return Response(get_all_objects(f'/{kind}/delta', r.args.get('since')), content_type=CT)


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
