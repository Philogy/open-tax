from collections import namedtuple
from enum import Enum


class AssetDirection(Enum):
    In = 1
    Out = -1


Atom = namedtuple(
    'Atom',
    [
        'identifier',
        'quantifier',
        'direction',
        'timestamp',
        'metadata'
    ]
)
