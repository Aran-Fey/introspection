
import inspect

__all__ = ['CallFrame']


class CallFrame:
    """
    Represents a call frame - an element of the call stack.
    It keeps track of local and closure variables.

    Note that storing CallFrames in variables can create reference
    cycles where a frame contains a reference to itself. To avoid
    this, CallFrames can be used as context managers - upon exit,
    the reference to the underlying frame object is released::

        with CallFrame.current() as frame:
            ...  # do stuff with the frame
        # at this point, the frame has become unusable
    """

    def __init__(self, frame):
        self.__frame = frame

    @classmethod
    def current(cls) -> 'CallFrame':
        """
        Retrieves the current call frame.

        :return: The current call frame
        """
        return cls(inspect.currentframe().f_back)

    def __getattr__(self, attr):
        return getattr(self.__frame, attr)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__frame = None

    @property
    def parent(self):
        """
        Returns the next frame one level higher on the call stack.
        """
        return self.__frame.f_back

    @property
    def builtins(self):
        """
        The builtins seen by this frame
        """
        return self.__frame.f_builtins

    @property
    def globals(self):
        """
        The global scope seen by this frame
        """
        return self.__frame.f_globals

    @property
    def locals(self):
        """
        The frame's local variable scope
        """
        return self.__frame.f_locals

    @property
    def code(self):
        """
        The code object being executed in this frame
        """
        return self.__frame.f_code

    @property
    def filename(self):
        """
        The name of the file in which this frame's code was defined
        """
        return self.code.co_filename

    def resolve_name(self, name):
        """
        Resolves a variable name, returning the variable's value.

        .. note:: Closure variables don't have a named associated with them,
                which means they cannot be looked up with this function.

                This includes variables marked as :code:`nonlocal`.

        :return: The value mapped to the given name
        :raises NameError: if no matching variable is found
        """
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
        """
        Finds and returns the function in which this CallFrame was called.

        :return: The calling function object
        """
        funcname = self.code.co_name

        parent = self.parent
        try:
            return parent.resolve_name(funcname)
        except NameError:
            return None
        finally:
            del parent
