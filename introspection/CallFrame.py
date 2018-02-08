
__all__ = ['CallFrame']


class CallFrame:
    def __init__(self, frame):
        self.__frame = frame

    def __getattr__(self, attr):
        return getattr(self.__frame, attr)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__frame = None

    @property
    def parent(self):
        return self.__frame.f_back

    @property
    def builtins(self):
        return self.__frame.f_builtins

    @property
    def globals(self):
        return self.__frame.f_globals

    @property
    def locals(self):
        return self.__frame.f_locals

    @property
    def code(self):
        return self.__frame.f_code

    @property
    def filename(self):
        return self.code.co_filename

    def resolve_name(self, name):
        try:
            return self.locals[name]
        except NameError:
            pass

        try:
            return self.globals[name]
        except NameError:
            pass

        try:
            return self.builtins[name]
        except NameError:
            pass

        raise NameError(name)

    def get_surrounding_function(self):
        funcname = self.code.co_name

        parent = self.parent
        try:
            return parent.resolve_name(funcname)
        except NameError:
            return None
        finally:
            del parent
