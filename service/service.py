import logging
import os
import json
from flask import Flask, Response, request as r
from user_dao import get_all_users, create_user_from_array
from group_dao import get_all_groups
from dao_helper import init_dao
from logger_helper import log_request

APP = Flask(__name__)
LOG_LEVEL = os.environ.get('LOG_LEVEL', "INFO")
PORT = int(os.environ.get('PORT', '5000'))

env = os.environ.get


@APP.route('/datasets/user/entities', methods=['GET'])
@log_request
def list_users():
    """
    Endpoint to fetch all users from Azure AD via MS graph API
    :request_argument since - delta token returned from last request (if exist)
    :return: JSON array with fetched users
    """
    init_dao(env('client_id'), env('client_secret'), env('tenant_id'))
    return Response(get_all_users(), content_type='application/json')


@APP.route('/datasets/group/entities')
@log_request
def list_groups():
    """
    Endpoint to fetch all groups from Azure AD via MS graph API
    :request_argument since - delta token returned from last request (if exist)
    :return: JSON array with fetched groups
    """
    init_dao(env('client_id'), env('client_secret'), env('tenant_id'))
    return Response(get_all_groups(r.args.get('since')), content_type='application/json')


@APP.route('/datasets/user', methods=['POST'])
@log_request
def post_users():
    init_dao(env('client_id'), env('client_secret'), env('tenant_id'))
    create_user_from_array(json.loads(r.data))
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
