# -*- coding: utf-8 -*-
# Author: Álvaro Parafita (parafita.alvaro@gmail.com)


def try_again_dec(*exceptions, retry=1):
    """
        Decorator to execute a function as many times as needed, 
        with a top limit in retry + 1 times,
        whenever we get an exception from the types detailed.
        If no exception happens, it doesn't reexecute the function.
        If some other exception than those specified is raised, 
        it won't be catched.

        If retry < 0, infinite loop while an exception inside "exceptions"
        is raised.

        If no exceptions are passed, Exception is the default.
    """

    exceptions = exceptions or (Exception,)

    def decorator(func):
        from functools import wraps
        
        @wraps(func)
        def _func(*args, **kwargs):
            infinite = retry < 0
            iters = 1 if infinite else retry + 1

            while True:
                exc = None
                for _ in range(iters):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        print("Exception raised: {}".format(repr(e)))
                        exc = e

                # Exception occured and we made too many retries
                if not infinite:
                    raise exc

                # else, try again
        
        return _func

    return decorator


def ncalls(n, after, *after_args, **after_kwargs):
    """
        Decorator to call a method with name 'after',
        after n calls to the decorated function.
        
        This decorator is only for bound methods, 
        meaning first argument in function must be self.
        
        The rest of the parameters will be passed to after_func.
    """
    
    from functools import wraps
    
    def dec(func):
        
        count = [0] # count needs to be mutable to use it like this
        @wraps(func)
        def f(self, *args, **kwargs):
            count[0] += 1
            res = func(self, *args, **kwargs)
            
            if count[0] >= n:
                count[0] = 0
                getattr(self, after)(*after_args, **after_kwargs)
            
            return res
        
        f._ncalls = count
        return f
    
    return dec