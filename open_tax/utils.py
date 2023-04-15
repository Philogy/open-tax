import requests
from toolz import curry
from decimal import Decimal


def hex_to_int(s: str) -> int:
    if not s.startswith('0x'):
        raise ValueError(f'Expected "{s}" to start with 0x')
    return int(s[2:], 16)


def alchemy_post(base_url, api_key, method, *params):
    res = requests.post(
        f'{base_url}/{api_key}',
        headers={
            'accept': 'application/json',
            'content-type': 'application/json'
        },
        json={
            'id': 1,
            'jsonrpc': '2.0',
            'method': method,
            'params': params
        }
    )
    return res.json(parse_float=Decimal)


@curry
def objset(k, v, obj):
    if callable(v):
        obj[k] = v(obj)
    else:
        obj[k] = v
    return obj
