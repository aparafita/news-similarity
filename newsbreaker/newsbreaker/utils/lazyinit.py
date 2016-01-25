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
            self.__args = args
            self.__kwargs = kwargs
            self.__initiated = False


        def __doinit__(self):
            args = object.__getattribute__(self, '_LazyInit__args')
            kwargs = object.__getattribute__(self, '_LazyInit__kwargs')

            del self.__args
            del self.__kwargs
            self.__initiated = True

            super().__init__(*args, **kwargs)


        def __getattribute__(self, name):
            if object.__getattribute__(self, '_LazyInit__initiated'):
                return object.__getattribute__(self, name)
            else:
                doinit = object.__getattribute__(self, '__doinit__')

                if name == '__doinit__':
                    return doinit
                else:
                    doinit()

                return object.__getattribute__(self, name)

    LazyInit.__name__ = cls.__name__
    LazyInit.__doc__ = cls.__doc__

    return LazyInit