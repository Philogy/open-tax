from collections import namedtuple
from enum import Enum

Effect = namedtuple(
    'Effect',
    ['rem', 'components', 'timestamp', 'id', 'ref', 'payee', 'description']
)

Suggestion = namedtuple('Suggestion', ['parent', 'child'])


class Remainder(Enum):
    TxFee = 'TX_FEE'
    BaseIncome = 'BASE_INCOME'  # Basic Income
    AssetChange = 'ASSET_CHANGE'  # Asset P&L
    AssetReturn = 'ASSET_RETURN'  # Asset Returns (Lending, Staking)
    Loss = 'LOSS'


Disposal = namedtuple('Disposal', ['asset', 'quantifier'])
Acquisition = namedtuple('Acquisition', ['asset', 'quantifier'])
