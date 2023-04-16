from typing import Union
from collections import defaultdict
from decimal import Decimal
from datetime import datetime
from beancount.core.data import Transaction, Posting, Cost, new_metadata, Open, Booking
from beancount.core.amount import Amount

from ..atomizers.base import AssetId, AssetSymbol, AssetContract
from ..contextualizers.base import Effect, Acquisition, Disposal
from .prices.coingecko import get_price_over_range
from .prices.utils import get_lin_avg_price, Price
from .base import assetid_to_coingecko

'''
For each effect:
    1. For each effe

'''


Range = tuple[Union[int, None], Union[int, None]]

CONTRACT_SYMBOLS = {
    ('ethereum', '0x57f1887a8bf19b14fc0df6fd9b2acc9af147ea85'): 'ENS'
}


def join_range(r: Range, new_val: int) -> Range:
    start, end = r
    if start is None or end is None:
        return (new_val, new_val)

    return min(start, new_val), max(end, new_val)


def widen_range(r: Range, ext: int) -> Range:
    start, end = r
    assert start is not None and end is not None
    return (start - ext, end + ext)


class BasicRealizer:
    def __init__(self, base_currency_account, asset_account, rem_accounts, base_currency):
        self.base_currency_account = base_currency_account
        self.asset_account = asset_account
        self.rem_accounts = rem_accounts
        self.base_currency = base_currency.upper()

    def realize(self, effects: list[Effect]) -> list[tuple]:
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

        for assetid, r in asset_time_ranges.items():
            asset_time_ranges[assetid] = widen_range(r, 12 * 60 * 60)

        asset_prices = {
            asset: get_price_over_range(
                assetid_to_coingecko(asset),
                self.base_currency.lower(),
                start,
                end
            )
            for asset, (start, end) in asset_time_ranges.items()
        }

        txs = []

        for effect in effects:
            bean_tx = self.effect_to_bean_tx(asset_prices, effect)
            if bean_tx is not None:
                txs.append(bean_tx)
        txs.sort(key=lambda tx: tx.date)

        first_day = txs[0].date
        accounts = {
            posting.account
            for tx in txs
            for posting in tx.postings
        }

        entries = [
            Open(
                None,
                first_day,
                account,
                None,
                Booking.FIFO if account == self.asset_account else Booking.STRICT
            )
            for account in accounts
        ]
        entries.extend(txs)

        return entries

    def effect_to_bean_tx(self, asset_prices: dict[AssetId, list[Price]], effect: Effect) -> Union[Transaction, None]:
        asset_to_price = None
        price = None
        needs_alt_price = False
        total_amount = Decimal(0)
        total_in_value = Decimal(0)

        date = datetime.fromtimestamp(effect.timestamp)

        # Get Acquisition Prices
        for comp in effect.components:
            asset_symbol, _ = self.assetid_to_descriptors(comp.asset)
            if isinstance(comp, Acquisition) and asset_symbol != self.base_currency:
                if asset_to_price is not None and comp.asset != asset_to_price:
                    raise TypeError(
                        f'Can only price 1 Acquisition asset per effect: {effect}'
                    )
                asset_to_price = comp.asset

                prices = asset_prices.get(comp.asset)
                if prices is None:
                    needs_alt_price = True
                    total_amount += comp.quantifier
                else:
                    price, _, _ = get_lin_avg_price(prices, date)

        if needs_alt_price:
            if total_amount == 0:
                raise ValueError(
                    f'Needs Alt Price For 0 Acqusition of {asset_to_price}'
                )
            total_in_value = Decimal(0)
            for comp in effect.components:
                if isinstance(comp, Disposal):
                    asset_symbol, _ = self.assetid_to_descriptors(comp.asset)
                    if asset_symbol == self.base_currency:
                        total_in_value += comp.quantifier
                        continue
                    prices = asset_prices.get(comp.asset)
                    if prices is None:
                        print(
                            f'WARNING: Required Alt Price But Couldn\'t Price Disposal {comp.asset}'
                        )
                        return None
                    disp_price, _, _ = get_lin_avg_price(prices, date)
                    if disp_price is None:
                        print(f'comp.asset: {comp.asset}')
                        print(f'prices: {prices}')
                        print(f'date: {date.strftime("%Y-%m-%d")}')
                    total_in_value += disp_price * comp.quantifier
            price = total_in_value / total_amount

        postings = []
        for comp in effect.components:
            if isinstance(comp, Disposal):
                num = -comp.quantifier
            elif isinstance(comp, Acquisition):
                num = comp.quantifier
            else:
                raise TypeError(f'Unsupported component {comp}')
            asset_symbol, tag = self.assetid_to_descriptors(comp.asset)
            cost = None
            if asset_symbol == self.base_currency:
                account = self.base_currency_account
            else:
                account = self.asset_account
                if isinstance(comp, Disposal):
                    cost = Cost(None, None, None, tag)
                elif isinstance(comp, Acquisition):
                    cost = Cost(price, self.base_currency, None, tag)

            postings.append(Posting(
                account,
                Amount(num, asset_symbol),
                cost,
                None,
                None,
                None
            ))
        postings.append(Posting(
            self.rem_accounts[effect.rem.parent], None, None, None, None, None
        ))

        meta = {
            'time': date.strftime('%H:%M:%S')
        }
        if effect.ref is not None:
            meta['ref'] = effect.ref

        return Transaction(
            new_metadata(None, None, meta),
            date.date(),
            '*',
            effect.payee,
            effect.description,
            frozenset(),
            frozenset(),
            postings
        )

    def assetid_to_descriptors(self, assetid: AssetId) -> tuple[str, Union[str, None]]:
        if isinstance(assetid.main, AssetSymbol):
            symbol = assetid.main.symbol
        elif isinstance(assetid.main, AssetContract):
            chain, addr = assetid.main
            symbol = CONTRACT_SYMBOLS.get((chain, addr))
            if symbol is None:
                symbol = f'UNK-{chain}-{addr[:8]}-{addr[-6:]}'.upper()
        else:
            raise TypeError(f'Unrecognized AssetId.main: {assetid.main}')

        if assetid.sub is None:
            tag = None
        else:
            tag = f'id:{assetid.sub}'

        return symbol, tag
