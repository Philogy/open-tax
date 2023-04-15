from decimal import Decimal
from ..utils import alchemy_post, hex_to_int
from .base import (BaseAtomizer, Atom, AssetDirection, PurposeHint, AssetId, AssetSymbol,
                   AssetContract, AssetType)


class AlchemyAtomizer(BaseAtomizer):
    def atomize(self, raw_entries: list[dict], params: dict) -> list[Atom]:
        chain = params['chain']

        return [*self._extract_atoms(raw_entries, chain)]

    def _extract_atoms(self, raw_entries: list[dict], chain: str):
        for entry in raw_entries:
            if entry['type'] == 'receipt':
                wei_fee = hex_to_int(entry['effectiveGasPrice'])\
                    * hex_to_int(entry['gasUsed'])
                yield Atom(
                    AssetId(
                        AssetSymbol(entry['asset']),
                        None,
                        AssetType.Fungible
                    ),
                    Decimal(wei_fee) / Decimal(10**18),
                    AssetDirection.Out,
                    entry['timestamp'],
                    PurposeHint.TxFee,
                    f'{chain}/{entry["transactionHash"]}',
                    {
                        'chain': chain,
                        **entry
                    }
                )
            elif entry['type'] in 'from_transfer':
                yield from self._extract_transfer_atoms(entry, chain, AssetDirection.Out)
            elif entry['type'] in 'to_transfer':
                yield from self._extract_transfer_atoms(entry, chain, AssetDirection.In)
            else:
                raise TypeError(f'Unrecognized entry type "{entry["type"]}"')

    def _extract_transfer_atoms(self, entry, chain, asset_direction: AssetDirection):
        identifier, quantifier = self._get_atom_value(chain, entry)
        if quantifier != 0:
            yield Atom(
                identifier,
                quantifier,
                asset_direction,
                entry['timestamp'],
                PurposeHint.Unknown,
                f'{chain}/{entry["hash"]}',
                {
                    'chain': chain,
                    **entry
                }
            )

    def _get_atom_value(self, chain, entry) -> tuple[AssetId, Decimal]:
        if entry['category'] == 'erc721':
            asset_contract = entry['rawContract']['address']
            return AssetId(AssetContract(chain, asset_contract), entry['tokenId'], AssetType.NonFungible), Decimal(1)
        elif entry['category'] in ('external', 'internal'):
            return AssetId(AssetSymbol(entry['asset']), None, AssetType.Fungible), entry['value']
        elif entry['category'] == 'erc20':
            asset_contract = entry['rawContract']['address']
            return AssetId(AssetContract(chain, asset_contract), None, AssetType.Fungible), entry['value']
        else:
            raise TypeError(
                f'Alchemy transfer category "{entry["category"]}" not implemented yet'
            )
