import copy
import threading


class Scope:
    def __init__(self):
        self.user = None
        self.tags = {}
        self.extras = {}
        self.breadcrumbs = []
        self.request = {}
        self.flag = None
        self.url = None
        self.channel = None
        self.dir = None

    def set_user(self, user):
        self.user = user

    def set_tag(self, key, value):
        self.tags[key] = value

    def set_extra(self, key, value):
        self.extras[key] = value

    def add_breadcrumb(self, category, message, level, data=None):
        self.breadcrumbs.append({
            'category': category,
            'message': message,
            'level': level,
            'data': data or {}
        })

    def set_request_data(self, data):
        self.request = data

    def clear_request_data(self):
        self.request = {}

    def set_flag(self, flag):
        self.flag = flag

    def set_url(self, url):
        self.url = url

    def set_channel(self, channel):
        self.channel = channel

    def set_dir(self, dir):
        self.dir = dir

    def get_event_data(self):
        data = {}

        if self.tags:
            params = []
            for key, value in self.tags.items():
                params.append({
                    'name': key,
                    'value': value
                })
            data['params'] = params

        if self.user:
            data['user'] = self.user

        if self.flag:
            data['flag'] = self.flag

        if self.url:
            data['url'] = self.url

        if self.channel:
            data['channel'] = self.channel

        if self.dir:
            data['dir'] = self.dir

        return data

    def clear(self):
        self.user = None
        self.tags = {}
        self.extras = {}
        self.breadcrumbs = []
        self.request = {}
        self.flag = None
        self.url = None
        self.channel = None
        self.dir = None


class Context:
    def __init__(self):
        self._global_scope = Scope()
        self._scopes = []
        self._stack = threading.local()

    @property
    def current_scope(self):
        if not hasattr(self._stack, 'stack'):
            self._stack.stack = []

        if not self._stack.stack:
            return self._global_scope

        return self._stack.stack[-1]

    def push_scope(self):
        if not hasattr(self._stack, 'stack'):
            self._stack.stack = []

        scope = Scope()

        scope.user = copy.deepcopy(self._global_scope.user)
        scope.tags = copy.deepcopy(self._global_scope.tags)
        scope.extras = copy.deepcopy(self._global_scope.extras)
        scope.breadcrumbs = copy.deepcopy(self._global_scope.breadcrumbs)
        scope.request = copy.deepcopy(self._global_scope.request)
        scope.flag = self._global_scope.flag
        scope.url = self._global_scope.url
        scope.channel = self._global_scope.channel
        scope.dir = self._global_scope.dir

        self._stack.stack.append(scope)
        return scope

    def pop_scope(self):
        if not hasattr(self._stack, 'stack'):
            return

        if self._stack.stack:
            self._stack.stack.pop()

    def clear_all(self):
        self._global_scope.clear()
        if hasattr(self._stack, 'stack'):
            self._stack.stack = []

    def set_user(self, user):
        self.current_scope.set_user(user)

    def set_tag(self, key, value):
        self.current_scope.set_tag(key, value)

    def set_extra(self, key, value):
        self.current_scope.set_extra(key, value)

    def add_breadcrumb(self, category, message, level, data=None):
        self.current_scope.add_breadcrumb(category, message, level, data)

    def set_request_data(self, data):
        self.current_scope.set_request_data(data)

    def clear_request_data(self):
        self.current_scope.clear_request_data()

    def get_event_data(self):
        return self.current_scope.get_event_data()

    @property
    def user(self):
        return self.current_scope.user

    @property
    def tags(self):
        return self.current_scope.tags

    @property
    def extras(self):
        return self.current_scope.extras

    @property
    def breadcrumbs(self):
        return self.current_scope.breadcrumbs

    @property
    def request(self):
        return self.current_scope.request

    def set_url(self, url):
        self.current_scope.set_url(url)
