from typing import Union
from ..atomizers.base import AssetId, AssetSymbol


SYMBOL_TO_COINGECKO = {
    'ETH': 'ethereum'
}


def assetid_to_coingecko(asset_id: AssetId) -> Union[str, None]:
    if isinstance(asset_id.main, AssetSymbol)\
            and asset_id.sub is None:
        return SYMBOL_TO_COINGECKO.get(asset_id.main.symbol)
    return None
