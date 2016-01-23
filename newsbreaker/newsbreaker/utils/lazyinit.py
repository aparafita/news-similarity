# -*- coding: utf-8 -*-
# Author: Álvaro Parafita (parafita.alvaro@gmail.com)


def lazyinit(cls):
    """
        Given the class to instantiate,
        it creates a new class that inherits it
        and delays the __init__ call
        until this instance is used in any possible way.
    """

    class LazyInit(cls):

        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs


        def __doinit__(self):
            self.__class__ = cls
            self.__init__(*self.args, **self.kwargs)

            del self.args
            del self.kwargs


        def __getattribute__(self, name):
            doinit = object.__getattribute__(self, '__doinit__')

            if name == '__doinit__':
                return doinit
            else:
                doinit()

            return getattr(self, name)
            

        # The following methods need to be overriden to avoid 
        # calling them directly, without passing through __getattribute__,
        # even if we define some of them with only a pass
        def __delattr__(self, name):
            self.__doinit__()
            delattr(self, name)

        def __del__(self):
            # don't do __doinit__ here. We're destroying the object
            del self

        def __repr__(self):
            self.__doinit__()
            return repr(self)

        def __str__(self):
            self.__doinit__()
            return str(self)

        def __bytes__(self):
            self.__doinit__()
            return bytes(self)

        def __format__(self, format_spec):
            self.__doinit__()
            return format(self, format_spec)

        def __lt__(self, other):
            self.__doinit__()
            return self < other

        def __le__(self, other):
            self.__doinit__()
            return self <= other

        def __eq__(self, other):
            self.__doinit__()
            return self == other

        def __ne__(self, other):
            self.__doinit__()
            return self != other

        def __gt__(self, other):
            self.__doinit__()
            return self > other

        def __ge__(self, other):
            self.__doinit__()
            return self >= other

        def __hash__(self):
            self.__doinit__()
            return hash(self)

        def __bool__(self):
            self.__doinit__()
            return bool(self)

        def __dir__(self):
            self.__doinit__()
            return dir(self)

        def __call__(self, *args, **kwargs):
            self.__doinit__()
            return self(*args, **kwargs)

        def __len__(self):
            self.__doinit__()
            return len(self)

        def __getitem__(self, key):
            self.__doinit__()
            return self[key]

        def __setitem__(self, key, value):
            self.__doinit__()
            self[key] = value

        def __delitem__(self, key):
            self.__doinit__()
            del self[key]

        def __iter__(self):
            self.__doinit__()
            return iter(self)

        def __reversed__(self):
            self.__doinit__()
            return reversed(self)

        def __contains__(self, item):
            self.__doinit__()
            return item in self

        def __add__(self, other):
            self.__doinit__()
            return self + other

        def __sub__(self, other):
            self.__doinit__()
            return self - other

        def __mul__(self, other):
            self.__doinit__()
            return self * other

        def __truediv__(self, other):
            self.__doinit__()
            return self / other

        def __floordiv__(self, other):
            self.__doinit__()
            return self // other

        def __mod__(self, other):
            self.__doinit__()
            return self % other

        def __divmod__(self, other):
            self.__doinit__()
            return divmod(self, other)

        def __pow__(self, other, *modulo):
            self.__doinit__()
            return self.__pow__(other, *modulo)

        def __lshift__(self, other):
            self.__doinit__()
            return self << other

        def __rshift__(self, other):
            self.__doinit__()
            return self >> other

        def __and__(self, other):
            self.__doinit__()
            return self & other

        def __xor__(self, other):
            self.__doinit__()
            return self ^ other

        def __or__(self, other):
            self.__doinit__()
            return self | other

        def __radd__(self, other):
            self.__doinit__()
            return self + other

        def __rsub__(self, other):
            self.__doinit__()
            return self - other

        def __rmul__(self, other):
            self.__doinit__()
            return self * other

        def __rtruediv__(self, other):
            self.__doinit__()
            return self / other

        def __rfloordiv__(self, other):
            self.__doinit__()
            return self // other

        def __rmod__(self, other):
            self.__doinit__()
            return self % other

        def __rdivmod__(self, other):
            self.__doinit__()
            return divmod(self, other)

        def __rpow__(self, other):
            self.__doinit__()
            return self ** other

        def __rlshift__(self, other):
            self.__doinit__()
            return self << other

        def __rrshift__(self, other):
            self.__doinit__()
            return self >> other

        def __rand__(self, other):
            self.__doinit__()
            return self & other

        def __rxor__(self, other):
            self.__doinit__()
            return self ^ other

        def __ror__(self, other):
            self.__doinit__()
            return self | other

        def __iadd__(self, other):
            self.__doinit__()
            self += other

        def __isub__(self, other):
            self.__doinit__()
            self -= other

        def __imul__(self, other):
            self.__doinit__()
            self *= other

        def __itruediv__(self, other):
            self.__doinit__()
            self /= other

        def __ifloordiv__(self, other):
            self.__doinit__()
            self //= other

        def __imod__(self, other):
            self.__doinit__()
            self %= other

        def __ipow__(self, other, *modulo):
            self.__doinit__()
            self.__ipow__(other, *modulo)

        def __ilshift__(self, other):
            self.__doinit__()
            self <<= other

        def __irshift__(self, other):
            self.__doinit__()
            self >>= other

        def __iand__(self, other):
            self.__doinit__()
            self &= other

        def __ixor__(self, other):
            self.__doinit__()
            self ^= other

        def __ior__(self, other):
            self.__doinit__()
            self |= other

        def __neg__(self):
            self.__doinit__()
            return -self

        def __pos__(self):
            self.__doinit__()
            return +self

        def __abs__(self):
            self.__doinit__()
            return abs(self)

        def __invert__(self):
            self.__doinit__()
            return ~self

        def __complex__(self):
            self.__doinit__()
            return complex(self)

        def __int__(self):
            self.__doinit__()
            return int(self)

        def __float__(self):
            self.__doinit__()
            return float(self)

        def __round__(self, *n):
            self.__doinit__()
            return round(self)

        def __index__(self):
            self.__doinit__()
            return self.__index__()

        def __enter__(self):
            self.__doinit__()
            return self.__enter__()

        def __exit__(self, exc_type, exc_value, traceback):
            self.__doinit__()
            return self.__exit__(exc_type, exc_value, traceback)

    LazyInit.__name__ = cls.__name__
    LazyInit.__doc__ = cls.__doc__

    return LazyInit