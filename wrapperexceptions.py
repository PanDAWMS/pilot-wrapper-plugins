#!/usr/bin/env python 

''' Exception classes for wrapper '''


class WrapperException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class WrapperExceptionSource(Exception):
    def __init__(self, value):
        self.value = "setup file %s does not exist " %value
    def __str__(self):
        return repr(self.value)

class WrapperExceptionSourceFail(Exception):
    def __init__(self, value):
        self.value = "sourcing setup file %s failed" %value
    def __str__(self):
        return repr(self.value)
