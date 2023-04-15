import json
import requests
from decimal import Decimal
from datetime import datetime
from .utils import Price, get_lin_avg_price

COINGECKO_BASE = 'https://api.coingecko.com/api'


def get(endpoint, params={}, parse_int=None, **kwarg_params):
    res = requests.get(
        f'{COINGECKO_BASE}/{endpoint}',
        {**params, **kwarg_params}
    )
    return json.loads(res.text, parse_float=Decimal, parse_int=parse_int)


def _validate_single_gecko_input(f):
    def gecko_fn(coin_id, vs_currency, *args, **kwargs):
        assert ',' not in coin_id, 'Provide single, unseparated'
        assert ',' not in vs_currency, 'Provide single, unseparated'
        return f(coin_id, vs_currency, *args, **kwargs)
    return gecko_fn


@_validate_single_gecko_input
def get_price_now(coin_id, vs_currency):
    res = get(
        'v3/simple/price',
        ids=coin_id,
        vs_currencies=vs_currency
    )
    return res.get(coin_id, dict()).get(vs_currency)


@_validate_single_gecko_input
def get_price_over_range(coin_id, vs_currency, start, end):
    res = get(f'v3/coins/{coin_id}/market_chart/range', {
        'vs_currency': vs_currency,
        'from': start,
        'to': end
    }, parse_int=int)
    return [
        Price(price, datetime.fromtimestamp(timestamp / 1000))
        for timestamp, price in res.get('prices')
    ]


HISTORIC_LIN_RADIUS = 12 * 60 * 60


def get_historic_lin_avg_price(coin_id, vs_currency, time):
    prices = get_price_over_range(
        coin_id,
        vs_currency,
        time.timestamp() - HISTORIC_LIN_RADIUS,
        time.timestamp() + HISTORIC_LIN_RADIUS
    )
    return get_lin_avg_price(prices, time)


def get_ticker(coin_id):
    res = get(f'v3/coins/list', include_platform=True)
    for asset in res:
        if asset['id'] == coin_id:
            return asset['symbol'].upper()
    raise ValueError(f'No trustworthy ticker found for "{coin_id}"')


if __name__ == '__main__':
    target = datetime.now().timestamp() - 2 * 365 * 24 * 60 * 60
    print(f'datetime.fromtimestamp(target): {datetime.fromtimestamp(target)}')
    price, d1, d2 = get_historic_lin_avg_price('ethereum', 'eur', target)
    print(f'price: {price}')
    print(f'd1: {d1}')
    print(f'd2: {d2}')
