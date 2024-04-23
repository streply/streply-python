import logging

logger = logging.getLogger('streply')

def parseParams(params: object):
    output = []

    for param in params:
        output.append({'name': param, 'value': params[param]})

    return output
