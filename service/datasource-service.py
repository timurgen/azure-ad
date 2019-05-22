from functools import wraps
from flask import Flask, request, Response, abort

import os
import requests

import json

import logging

import adal
import uuid

app = Flask(__name__)

logger = None

def datetime_format(dt):
    return '%04d' % dt.year + dt.strftime("-%m-%dT%H:%M:%SZ")


def to_transit_datetime(dt_int):
    return "~t" + datetime_format(dt_int)

class DataAccess:
    def __init__(self):
        self._entities = {"users": []}

    def get_entities(self, since, datatype, endpoint, token):
        if not datatype in self._entities:
            abort(404)

        return self.get_entitiesdata(datatype, since, endpoint, token)

    def get_entitiesdata(self, datatype, since, endpoint, token):

        entities = []


        if since is not None:
            endpoint = endpoint + "?$skiptoken=" + since

        http_headers = {'Authorization': 'Bearer ' + token["accessToken"],
                        'User-Agent': 'adal-python-sample',
                        'Accept': 'application/json',
                        'Content-Type': 'application/json',
                        'client-request-id': str(uuid.uuid4())}
        result = requests.get(endpoint, headers=http_headers, stream=False).json()

        skiptoken = None

        if "@odata.nextLink" in result:
            skiptoken = result["@odata.nextLink"].split("?$skiptoken=")[-1]

        if "value" in result:
            for e in result["value"]:

               # c = {k: v for k, v in c.items() if v}
                e.update({"_id": e["id"]})
                if skiptoken:
                    e.update({"_updated": "%s" % skiptoken})

                if "@removed" in e:
                    e.update({"_deleted": True})

                entities.append(e)


        return entities

data_access_layer = DataAccess()

def get_var(var):
    envvar = None
    if var.upper() in os.environ:
        envvar = os.environ[var.upper()]
    else:
        envvar = request.args.get(var)
    logger.info("Setting %s = %s" % (var, envvar))
    return envvar

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth:
            return authenticate()
        return f(*args, **kwargs)

    return decorated

@app.route('/<datatype>', methods=['GET'])
@requires_auth
def get_entities(datatype):
    since = request.args.get('since')
    authority_url = get_var('authority_url') or "https://login.microsoftonline.com"
    tenant = get_var('tenant') or "sesamdata.onmicrosoft.com"
    resource = get_var('resource') or "https://graph.microsoft.com"
    api_version = get_var('api_version') or "v1.0"

    endpoint = resource + '/' + api_version + '/' + datatype + "/delta"

    auth = request.authorization
    logger.info("User = %s" % (auth.username))
    auth_context = adal.AuthenticationContext(authority_url + "/" + tenant)
    token_response = auth_context.acquire_token_with_client_credentials(resource,
                                                                        auth.username, auth.password)


    entities = sorted(data_access_layer.get_entities(since, datatype, endpoint, token_response), key=lambda k: k["_updated"])

    return Response(json.dumps(entities), mimetype='application/json')



@app.route('/<datatype>', methods=['POST'])
@requires_auth
def receiver(datatype):
    # get entities from request and write each of them to a file
    entities = request.get_json()
    app.logger.info("Updating %s entities of type %s" % (len(entities), datatype))
    app.logger.debug(json.dumps(entities))

    authority_url = get_var('authority_url') or "https://login.microsoftonline.com"
    tenant = get_var('tenant') or "sesamdata.onmicrosoft.com"
    resource = get_var('resource') or "https://graph.microsoft.com"
    api_version = get_var('api_version') or "v1.0"

    endpoint = resource + '/' + api_version + '/' + datatype

    auth = request.authorization
    logger.info("User = %s" % (auth.username))
    auth_context = adal.AuthenticationContext(authority_url + "/" + tenant)
    token_response = auth_context.acquire_token_with_client_credentials(resource,
                                                                        auth.username, auth.password)

    transform(datatype, entities, endpoint, token_response)# create the response

    return Response("Thanks!", mimetype='text/plain')

def transform(datatype, entities, endpoint, token):
    global ids
    # create output directory
    c = None
    listing = []
    if not isinstance(entities, (list)):
        listing.append(entities)
    else:
        listing = entities
    for e in listing:
        del e["_id"]
        if not ("_deleted" in e and e["_deleted"]):
            if "id" in e:
                app.logger.debug("Update entity %s of type %s" % (e["id"], datatype))
                d = []
                for p in e.keys():
                    if p.startswith("_"):
                        d.append(p)
                for p in d:
                    del(e[p])

                http_headers = {'Authorization': 'Bearer ' + token["accessToken"],
                                'User-Agent': 'sesam',
                                'Accept': 'application/json',
                                'Content-Type': 'application/json',
                                'client-request-id': str(uuid.uuid4())}

                app.logger.debug("Payload: %s" % (json.dumps(e)))
                id = e["id"]
                del(e["id"])
                result = requests.patch(endpoint + "/" + id, json=e, headers=http_headers)

                if result.status_code >= 400:
                    app.logger.error("Result: %s - %s: %s" % (result.status_code, result.reason, result.json()))
                    result.raise_for_status()
                else:
                    app.logger.debug("Result: %s - %s" % (result.status_code, result.reason))

        if "_deleted" in e and e["_deleted"] :
            if "Id" in e:
                app.logger.info("Deleting entity %s of type %s" % (e["Id"],datatype))




if __name__ == '__main__':
    # Set up logging
    format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logger = logging.getLogger('salesforce-microservice')

    # Log to stdout
    stdout_handler = logging.StreamHandler()
    stdout_handler.setFormatter(logging.Formatter(format_string))
    logger.addHandler(stdout_handler)

    logger.setLevel(logging.DEBUG)

    app.run(debug=True, host='0.0.0.0')

