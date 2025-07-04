import sys
from typing import Dict, Any, Optional

from streply_sdk.utils.data_scrubbing import scrub_request_data, scrub_dict


def before_send_hook(event: Dict[str, Any], hint: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
    if hint is None:
        hint = {}

    if 'params' in event and isinstance(event['params'], list):
        params_dict = {}
        for param in event['params']:
            if 'name' in param and 'value' in param:
                params_dict[param['name']] = param['value']

        cleaned_params_dict = scrub_dict(params_dict)

        event['params'] = [
            {'name': key, 'value': value}
            for key, value in cleaned_params_dict.items()
        ]

    if 'requestParams' in event and isinstance(event['requestParams'], dict):
        event['requestParams'] = scrub_request_data(event['requestParams'])

    if 'user' in event and isinstance(event['user'], dict) and 'params' in event['user']:
        if isinstance(event['user']['params'], list):
            user_params_dict = {}
            for param in event['user']['params']:
                if 'name' in param and 'value' in param:
                    user_params_dict[param['name']] = param['value']

            cleaned_user_params_dict = scrub_dict(user_params_dict)

            event['user']['params'] = [
                {'name': key, 'value': value}
                for key, value in cleaned_user_params_dict.items()
            ]

    return event


def add_environment_data(event: Dict[str, Any]) -> Dict[str, Any]:
    if 'params' not in event:
        event['params'] = []

    import platform
    event['params'].append({
        'name': 'os',
        'value': platform.platform()
    })

    event['params'].append({
        'name': 'python',
        'value': platform.python_version()
    })

    event['params'].append({
        'name': 'interpreter',
        'value': sys.executable
    })

    return event
