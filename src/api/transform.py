'''
Validate and transform SmartAPI/OpenAPI v3 metadata for indexing
'''
import copy
import json
import base64
import gzip

import requests
import jsonschema

SMARTAPI_SCHEMA_URL = 'https://raw.githubusercontent.com/WebsmartAPI/smartAPI-editor/master/node_modules_changes/opanapi.json'


def encode_raw(metadata):
    '''return encoded and compressed metadata'''
    _raw = json.dumps(metadata).encode('utf-8')
    _raw = base64.urlsafe_b64encode(gzip.compress(_raw)).decode('utf-8')
    return _raw


def decode_raw(raw):
    _raw = gzip.decompress(base64.urlsafe_b64decode(raw)).decode('utf-8')
    return json.loads(_raw)


class APIMetadata:
    def __init__(self, metadata):
        self.schema = self.get_schema()
        self.metadata = metadata

    def get_schema(self):
        return json.loads(requests.get(SMARTAPI_SCHEMA_URL).text)

    def validate(self):
        '''Validate API metadata against JSON Schema.'''
        try:
            jsonschema.validate(self.metadata, self.schema)
        except jsonschema.ValidationError as e:
            return {"valid": False, "error": e.message}
        return {"valid": True}

    def _encode_raw(self):
        '''return encoded and compressed metadata'''
        _raw = json.dumps(self.metadata).encode('utf-8')
        _raw = base64.urlsafe_b64encode(gzip.compress(_raw)).decode('utf-8')
        return _raw

    def convert_es(self):
        '''convert API metadata for ES indexing.'''
        _d = copy.copy(self.metadata)

        # convert paths to a list of each path item
        _paths = []
        for path in _d['paths']:
            _paths.append({
                "path": path,
                "pathitem": _d['paths'][path]
            })
        _d['paths'] = _paths

        #include compressed binary raw metadata as "~raw"
        _d["~raw"] = encode_raw(self.metadata)
        return _d