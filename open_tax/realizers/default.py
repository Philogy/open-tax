from typing import Union
from collections import defaultdict
from beancount.core.data import Transaction
from beancount.core.amount import Amount

from ..atomizers.base import AssetId
from ..contextualizers.base import Effect, Remainder
from .prices.coingecko import get_price_over_range
from .prices.utils import get_lin_avg_price
from .base import assetid_to_coingecko

'''
For each effect:
    1. For each effe

'''


Range = tuple[Union[int, None], Union[int, None]]


def join_range(r: Range, new_val: int) -> Range:
    start, end = r
    if start is None or end is None:
        return (new_val, new_val)

    return min(start, new_val), max(end, new_val)


class BasicRealizer:
    def __init__(self, rem_accounts, base_currency):
        self.rem_accounts = rem_accounts
        self.base_currency = base_currency

    def realize(self, effects: list[Effect]) -> list[tuple]:
        txs = []

        asset_time_ranges: dict[AssetId, Range] = defaultdict(
            lambda: (None, None)
        )

        for effect in effects:
            for comp in effect.components:
                print(comp.asset)
                geckoid = assetid_to_coingecko(comp.asset)
                if geckoid is None:
                    continue
                r = asset_time_ranges[comp.asset]
                asset_time_ranges[comp.asset] = join_range(r, effect.timestamp)

        prices = {
            asset: get_price_over_range(
                assetid_to_coingecko(asset),
                self.base_currency.lower(),
                start,
                end
            )
            for asset, (start, end) in asset_time_ranges.items()
        }

        print(prices)

        return txs
