# Official Streply SDK for Python

## Getting started

### Install
```bash
pip install --upgrade streply-sdk
```

### Initialization
```python
from streply.streply import streply

streply('https://clientPublicKey@api.streply.com/projectId', {
    'environment': 'local',
    'release': 'my-project-name@2.3.12',
})
```

### Usage
```python
from streply.capture import exception

# handled exception
try:
    raise NotImplementedError("Not implemented error")
except Exception as e:
    exception(e)
    
# Streply will also capture unhandled exception
raise ValueError("Sorry, no numbers below zero")
```

Exception with error level:

```python
from streply.capture import exception
from streply.enum.level import level

try:
    raise NotImplementedError("Not implemented error")
except Exception as e:
    exception(e, {}, level.CRITICAL)
```

### Logs
```python
from streply.utils import logger

logger.debug("A debug message")
logger.info("An info message")
logger.warning("A warning message")
logger.error("An error message")
logger.critical("A critical message")
```

Adding params to log:

```python
from streply.utils import logger

logger.info("A info message", {
    'userName': 'Joey'
})
```

### Activity

```python
from streply.capture import activity

activity('auth.register', {
    'userName': 'Joey'
})
```


## Configuration

### Adding user data

```python
from streply.streply import streply

streply = streply('https://clientPublicKey@api.streply.com/projectId')
streply.set_user('ID')
# or with username
streply.set_user('ID', 'Joey')
```

or with parameters and name

```python
from streply.streply import streply

streply = streply('https://clientPublicKey@api.streply.com/projectId')
streply.set_user('ID', 'Joey', {
    'createdAt': '2022-11-10 15:10:32'
})
```

## Capture levels

- `level.CRITICAL`
- `level.HIGH`
- `level.NORMAL`
- `level.LOW`

