from flask import Flask, request, Response
import os
import requests
from requests_ntlm import HttpNtlmAuth
import logging
import json
from dotdictify import Dotdictify

app = Flask(__name__)
logger = None
format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logger = logging.getLogger('get-nested')

# Log to stdout
stdout_handler = logging.StreamHandler()
stdout_handler.setFormatter(logging.Formatter(format_string))
logger.addHandler(stdout_handler)
logger.setLevel(logging.DEBUG)


class DataAccess:

    def __get_all_entities(self, path, args):
        logger.info("Fetching data from url: %s", path)
        since = args.get("since")
        if since is not None:
            url = os.environ.get("base_url") + path + "?since=" + since
        else:
            logger.info("No since parameter defined, getting all entities")
            url = os.environ.get("base_url") + path

        if "username" not in os.environ or "password" not in os.environ:
            logger.error("missing username/password")

        req = requests.get(url, auth=HttpNtlmAuth(os.environ.get("username"), os.environ.get("password")))
        entities = json.loads(req.text)
        for entity in entities:
            yield get_user_profile(entity, args)


    def __get_entity_list(self, path, args):

        logger.info("Fetching data from url: %s", path)
        since = args.get("since")
        if since is not None:
            url = os.environ.get("base_url") + path +"?since=" + since
        else:
            url = os.environ.get("base_url") + path
        if "username" not in os.environ or "password" not in os.environ:
            logger.error("missing username/password")
            yield

        req = requests.get(url, auth=HttpNtlmAuth(os.environ.get("username"),os.environ.get("password")))
        for entity in json.loads(req.text):
            yield set_list_updated(entity, args)


        if req.status_code != 200:
            logger.error("Unexpected response status code: %d with response text %s" % (req.status_code, req.text))
            raise AssertionError("Unexpected response status code: %d with response text %s" % (req.status_code, req.text))


    def get_entity(self, path, args):
        print('getting entity')
        return self.__get_all_entities(path, args)

    def get_entity_list(self, path, args):
        print('getting list')
        return self.__get_entity_list(path, args)


data_access_layer = DataAccess()

def get_user_profile(entity,args):
    #This key_path defines where to get the ID that is required for the second enpoint request
    key_path = args.get("key_path")

    since_path = args.get("since_path")
    dict = Dotdictify(entity)
    since = dict.get(since_path)
    key = dict.get(key_path)

    url = os.environ.get("base_url") + os.environ.get("entity_url") + "?id=" + key
    req = requests.get(url, auth=HttpNtlmAuth(os.environ.get("username"), os.environ.get("password")))

    try:
        entities = json.loads(req.text)
    except ValueError:
        logger.info("Could not find entity for id: %s", key)
        return None
    else:
        if not isinstance(entities, list):
            entities = [entities]
        for entity in entities:
            if since_path is not None:
                entity["_updated"] = since

    return entity

def set_list_updated(entity, args):
    since_path = args.get("since_path")

    if since_path is not None:
        b = Dotdictify(entity)
        entity["_updated"] = b.get(since_path)

    return entity


def stream_json(clean):
    first = True
    yield '['
    for i, row in enumerate(clean):
        if not first:
            yield ','
        else:
            first = False
        yield json.dumps(row)
    yield ']'

@app.route("/entitylist", methods=["GET"])
def get_userlist():
    entities = data_access_layer.get_entity_list(os.environ.get("entitylist_url"), args=request.args)
    return Response(
        stream_json(entities),
        mimetype='application/json'
    )


@app.route("/entity", methods=["GET"])
def get_user():
    if request.args.get("key_path") is None:
        return Response (json.dumps([{'fault':'missing key_path'}]), mimetype='application/json', status=404)
    else:
        entities = data_access_layer.get_entity(os.environ.get("entitylist_url"), args=request.args)
        return Response(
            stream_json(entities),
            mimetype='application/json'
        )


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', threaded=True, port=os.environ.get('port',5000))
