import dataclasses


SomeTypeDefinedInParentsFile = int


@dataclasses.dataclass
class Parent:
    """
    This class is used to test whether the forward reference "SomeTypeDefinedInParentsFile" can be
    resolved from a child class, if the child class is defined in a different file.
    """

    foo: "SomeTypeDefinedInParentsFile"
