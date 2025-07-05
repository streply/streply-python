import json
import datetime
import uuid
from typing import Any, Dict, List


class StreamlyJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        if isinstance(obj, datetime.date):
            return obj.isoformat()
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, bytes):
            return obj.decode('utf-8', errors='replace')
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()

        try:
            return dict(obj)
        except (TypeError, ValueError):
            pass

        try:
            return str(obj)
        except (TypeError, ValueError):
            return repr(obj)


def to_json(data: Any) -> str:
    return json.dumps(data, cls=StreamlyJSONEncoder)


def from_json(data: str) -> Any:
    return json.loads(data)


def scrub_sensitive_data(data: Dict[str, Any], sensitive_keys: List[str] = None) -> Dict[str, Any]:
    if sensitive_keys is None:
        sensitive_keys = ['password', 'secret', 'token', 'api_key', 'apikey', 'auth']

    result = {}

    for key, value in data.items():
        contains_sensitive = False
        for sensitive_key in sensitive_keys:
            if sensitive_key.lower() in key.lower():
                contains_sensitive = True
                break

        if contains_sensitive:
            result[key] = '********'
        elif isinstance(value, dict):
            result[key] = scrub_sensitive_data(value, sensitive_keys)
        elif isinstance(value, list):
            result[key] = [
                scrub_sensitive_data(item, sensitive_keys) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value

    return result
