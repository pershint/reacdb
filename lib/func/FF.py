class FunctionalFunction(object):
    def __init__(self,func):
        self.func = func

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def __add__(self,other):
        def summed(*args, **kwargs):
            return self(*args, **kwargs) + other(*args, **kwargs)
        return summed

    def __mul__(self, other):
        def composed(*args, **kwargs):
            return self(other(*args, **kwargs))
        return composed

