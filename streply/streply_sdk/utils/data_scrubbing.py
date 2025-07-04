import re
from typing import Any, Dict, List

DEFAULT_SENSITIVE_KEYS = [
    'password', 'passwd', 'secret', 'token', 'api_key', 'apikey', 'auth',
    'credential', 'private', 'pwd', 'ssn', 'social_security', 'credit_card',
    'card', 'cvv', 'cvc', 'expiration', 'pin', 'passphrase', 'key'
]

CREDIT_CARD_PATTERN = re.compile(r'\b(?:\d[ -]*?){13,16}\b')

EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')


def scrub_dict(data: Dict[str, Any], sensitive_keys: List[str] = None) -> Dict[str, Any]:
    if sensitive_keys is None:
        sensitive_keys = DEFAULT_SENSITIVE_KEYS

    result = {}

    for key, value in data.items():
        contains_sensitive = any(sensitive_key.lower() in key.lower() for sensitive_key in sensitive_keys)

        if contains_sensitive:
            result[key] = '********'
        elif isinstance(value, dict):
            result[key] = scrub_dict(value, sensitive_keys)
        elif isinstance(value, list):
            result[key] = [
                scrub_dict(item, sensitive_keys) if isinstance(item, dict) else scrub_value(item)
                for item in value
            ]
        else:
            result[key] = scrub_value(value)

    return result


def scrub_value(value: Any) -> Any:
    if not isinstance(value, str):
        return value

    value = CREDIT_CARD_PATTERN.sub('****-****-****-****', value)

    return value


def scrub_request_data(request_data: Dict[str, Any]) -> Dict[str, Any]:
    result = {}

    if 'GET' in request_data:
        result['GET'] = scrub_dict(request_data['GET'])

    if 'POST' in request_data:
        result['POST'] = scrub_dict(request_data['POST'])

    if 'JSON' in request_data and request_data['JSON']:
        if isinstance(request_data['JSON'], dict):
            result['JSON'] = scrub_dict(request_data['JSON'])
        else:
            result['JSON'] = request_data['JSON']

    if 'headers' in request_data:
        headers = {}
        for key, value in request_data['headers'].items():
            if key.lower() in ('authorization', 'cookie', 'set-cookie', 'x-auth-token', 'x-api-key'):
                headers[key] = '********'
            else:
                headers[key] = value

        result['headers'] = headers

    for key, value in request_data.items():
        if key not in ('GET', 'POST', 'JSON', 'headers'):
            result[key] = value

    return result
