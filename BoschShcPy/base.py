from datetime import datetime

import dateutil.parser


class Base(object):
    def load_dict(self, data):
        for name, value in list(data.items()):
            if hasattr(self, name) and not callable(getattr(self, name)):
                setattr(self, name, value)

        return self

    def load(self, data):
        if isinstance(data, list):
            for elem in data:
                self.load_dict(elem)
        else:
#             print(data)
            self.load_dict(data)
        return self

    def get_id(self):
        raise NotImplementedError()

    def update(self):
        raise NotImplementedError()
    
    def update_from_query(self, query_result):
        raise NotImplementedError()
    
    @staticmethod
    def value_to_time(value, format='%Y-%m-%dT%H:%M:%S+00:00'):
        if value is not None:
            return dateutil.parser.parse(value).replace(microsecond=0)