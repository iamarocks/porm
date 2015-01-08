
class Validator(object):
    def __init__(self):
        pass

class ValidatorException(Exception):
    pass

class StringValidator(object):
    def __init__(self, min_length, max_length):
        self.min_length = min_length
        self.max_length = max_length

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value


    def validate(self):
        if len(self.value) > self.max_length or len(self.value) < self.min_length:
            return False
        else:
            return True
