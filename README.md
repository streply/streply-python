# Streply.com SDK for Python

**Streply.com** is a comprehensive error tracking and monitoring solution for applications.

Streply helps you identify, track, and resolve issues in your Python applications with minimal setup.

---

## Features

- **Automatic error tracking**: Capture unhandled exceptions and errors  
- **Custom event tracking**: Track custom events and messages  
- **User context**: Associate errors with specific users  
- **Breadcrumbs**: Track application flow leading up to errors  
- **Performance monitoring**: Measure and track performance of your application  
- **Context data**: Capture request data, environment variables, and more  
- **Data scrubbing**: Automatically scrub sensitive data from error reports  
- **Framework integrations**: Seamless integration with popular Python frameworks  

---

## Installation

Install the Streply SDK using pip:

```bash
pip install streply-sdk
```

## Framework-Specific Installation

For framework-specific integrations, install with the appropriate extras:

```bash
# Django integration
pip install streply-sdk[django]

# Flask integration
pip install streply-sdk[flask]

# FastAPI integration
pip install streply-sdk[fastapi]

# Bottle integration
pip install streply-sdk[bottle]

# Celery integration
pip install streply-sdk[celery]

# RQ (Redis Queue) integration
pip install streply-sdk[rq]
```

---

## Quick Start

```python
import streply_sdk

# Initialize the SDK with your DSN
streply_sdk.init(
    dsn="https://your-public-key@streply.com/your-project-id",
    environment="production",  # Optional
    release="1.0.0"            # Optional
)

# Capture exceptions
try:
    1 / 0
except Exception as e:
    streply_sdk.capture_exception()

# Capture custom messages
streply_sdk.capture_message("Something happened!", level="warning")

# Set user context
streply_sdk.set_user({
    "userId": "123",
    "userName": "johndoe",
    "params": [
        {"name": "email", "value": "john@example.com"}
    ]
})

# Add breadcrumbs to track application flow
streply_sdk.add_breadcrumb(
    category="auth",
    message="User logged in",
    level="info",
    data={"method": "google-oauth"}
)

# Performance monitoring
@streply_sdk.trace
def slow_function():
    # Your code here
    pass

# Or use context manager
with streply_sdk.trace_ctx(name="database-query", op="db.query"):
    # Your database query here
    pass
```

---

## Supported Frameworks

Streply automatically detects and integrates with the following frameworks:

- **Django**: Full request/response cycle tracking, user context, and middleware integration  
- **Flask**: Error handling, request tracking, and context management  
- **FastAPI**: Exception middleware, request middleware, and context tracking  
- **Bottle**: Error handling and request context tracking  
- **Celery**: Task failure handling, retry tracking, and task context  
- **RQ (Redis Queue)**: Job execution monitoring and failure tracking  
- **WSGI**: Generic WSGI application support  

---

## Configuration Options

```python
streply_sdk.init(
    dsn="https://your-public-key@streply.com/your-project-id",
    environment="production",          # Application environment
    release="1.0.0",                   # Release version
    send_default_pii=True,             # Whether to include PII data
    max_breadcrumbs=100,               # Maximum number of breadcrumbs to store
    sample_rate=1.0,                   # Event sampling rate (0.0 to 1.0)
    traces_sample_rate=1.0,            # Performance sampling rate (0.0 to 1.0)
    debug=False,                       # Enable debug mode
    integrations=[]                    # Custom integrations
)
```

---

## Context Management

Streply allows you to configure the scope for capturing additional context with errors:

```python
# Configure the scope
with streply_sdk.configure_scope() as scope:
    scope.set_tag("server", "web-1")
    scope.set_extra("database_connection", "healthy")

# Set tags directly
streply_sdk.set_tag("feature_enabled", True)

# Set extra data
streply_sdk.set_extra("cart_items", 5)
```

---

## Advanced Usage

### Custom Transport

```python
from streply_sdk.core.transport import Transport

class CustomTransport(Transport):
    def send(self, event):
        # Custom implementation
        pass

streply_sdk.init(
    dsn="https://your-public-key@streply.com/your-project-id",
    transport=CustomTransport(dsn="https://your-public-key@streply.com/your-project-id")
)
```

### Event Hooks

```python
def before_send(event, hint):
    # Modify event before sending
    if "password" in event.get("message", ""):
        return None  # Don't send events with passwords
    return event

streply_sdk.init(
    dsn="https://your-public-key@streply.com/your-project-id",
    hooks={
        "before_send": before_send
    }
)
```

---

## License

This SDK is distributed under the MIT license. See the [LICENSE](LICENSE) file for more information.