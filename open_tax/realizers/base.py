from typing import Union
from ..atomizers.base import AssetId, AssetSymbol, AssetContract, AssetType


SYMBOL_TO_COINGECKO = {
    'ETH': 'ethereum'
}


def assetid_to_coingecko(asset_id: AssetId) -> Union[str, None]:
    print(f'asset_id: {asset_id}')
    if isinstance(asset_id.main, AssetSymbol)\
            and asset_id.sub is None\
            and asset_id.atype == AssetType.Fungible:
        return SYMBOL_TO_COINGECKO.get(asset_id.main.symbol)
    return None
