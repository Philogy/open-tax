from .base import BaseCollector
from ..utils import alchemy_post, hex_to_int, objset


class AlchemyCollector(BaseCollector):
    CATEGORIES = [
        'external', 'internal', 'erc1155', 'erc20', 'erc721', 'specialnft'
    ]

    def __init__(self, alchemy_key: str, base_url: str, wallet_addresses: list[str]) -> None:
        if base_url[-1] == '/':
            base_url = base_url[:-1]
        self.base_url = base_url
        self.__api_key = alchemy_key
        self.wallets = wallet_addresses

    def collect(self) -> list[dict]:

        entries = []
        for wallet in self.wallets:
            print('fetching from transfers ...')
            from_transfers = self._query('alchemy_getAssetTransfers', {
                'fromAddress': wallet,
                'category': self.CATEGORIES,
                'excludeZeroValue': False

            })['result']['transfers']

            entries.extend(
                map(objset('type', 'from_transfer'), from_transfers)
            )

            print('fetching to transfers ...')

            to_transfers = self._query('alchemy_getAssetTransfers', {
                'toAddress': wallet,
                'category': self.CATEGORIES,
                'excludeZeroValue': False
            })['result']['transfers']
            entries.extend(
                map(objset('type', 'to_transfer'), to_transfers)
            )

            external_transfer_txids = {
                transfer['hash']: transfer
                for transfer in from_transfers
                if transfer['category'] == 'external'
            }
            print(f'fetching receipts ({len(external_transfer_txids)}) ...')

            receipts = [
                {
                    **self._query('eth_getTransactionReceipt', txid)['result'],
                    'asset': transfer['asset']
                }
                for txid, transfer in external_transfer_txids.items()
            ]
            entries.extend(map(objset('type', 'receipt'), receipts))

        block_numbers = set(map(self.get_entry_block, entries))
        print(f'fetching blocks ({len(block_numbers)}) ...')
        blocks = {
            block_num: self._query(
                'eth_getBlockByNumber',
                block_num,
                False
            )['result']
            for block_num in block_numbers
        }

        print('done')

        for entry in entries:
            block = blocks[self.get_entry_block(entry)]
            entry['timestamp'] = hex_to_int(block['timestamp'])

        return entries

    @staticmethod
    def get_entry_block(entry: dict) -> str:
        return entry[
            'blockNumber'
            if entry['type'] == 'receipt'
            else 'blockNum'
        ]

    def _query(self, method, *params):
        return alchemy_post(self.base_url, self.__api_key, method, *params)
