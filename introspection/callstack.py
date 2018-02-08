
import inspect


def get_current_class():
    """
    Returns the name of the current module and the name of the class that is currently being created.
    Has to be called in class-level code, for example:

    ::
        def deco(f):
            print(get_current_class())
            return f

        def deco2(arg):
            def wrap(f):
                print(get_current_class())
                return f
            return wrap

        class Foo:
            print(get_current_class())

            @deco
            def f(self):
                pass

            @deco2('foobar')
            def f2(self):
                pass
    """
    frame = inspect.currentframe()
    while True:
        frame = frame.f_back
        if frame is None:
            return None

        if '__module__' in frame.f_locals:
            break
    dict_ = frame.f_locals
    cls = (dict_['__module__'], dict_['__qualname__'])
    return cls
