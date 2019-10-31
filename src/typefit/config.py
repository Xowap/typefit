from dataclasses import dataclass

@dataclass
class Config:
    """
    Configuration for typefit function.

    Parameters
    ----------
    strict_mapping
        Boolean to enable strict model for :class:NamedTuple or :class:dataclass.
        Default `False`.
    """

    strict_mapping: bool = False
