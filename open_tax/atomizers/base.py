from abc import ABC, abstractmethod
from collections import namedtuple
from enum import Enum


class AssetDirection(Enum):
    In = 1
    Out = -1


class PurposeHint(Enum):
    Unknown = 'UNKNOWN'
    TxFee = 'TX_FEE'


Atom = namedtuple(
    'Atom',
    [
        'identifier',
        'quantifier',
        'direction',
        'timestamp',
        'purpose_hint',
        'txid',
        'metadata'
    ]
)


class AssetType(Enum):
    Fungible = 'FUNGIBLE'
    NonFungible = 'NonFungible'


AssetId = namedtuple('AssetId', ['main', 'sub', 'atype'])
AssetSymbol = namedtuple('AssetSymbol', ['symbol'])
AssetContract = namedtuple('AssetContract', ['chain', 'address'])


class BaseAtomizer(ABC):

    @abstractmethod
    def atomize(self, raw_entries: list[dict], params: dict) -> list[Atom]:
        pass
