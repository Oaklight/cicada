from typing import Protocol


class SupportStr(Protocol):
    """A protocol for objects that support conversion to a string.

    This protocol ensures that any implementing class has a `__str__`
    method, allowing the object to be represented as a string.

    Example:
        This can be implemented in a class as follows:

        ```
        class MyClass:
            def __str__(self) -> str:
                return "MyClass string representation"
        ```

    Returns:
        str: The string representation of the object when `__str__` is called.
    """

    def __str__(self) -> str: ...
