from typing import Union, Generator

from ..atomizers.base import Atom, AssetDirection, PurposeHint
from .base import Effect, Acquisition, Disposal, Suggestion, Remainder
from collections import defaultdict
from decimal import Decimal
from toolz import groupby


def atom_to_asset_change(atom: Atom) -> Union[Acquisition, Disposal]:
    if atom.direction == AssetDirection.Out:
        return Disposal(atom.identifier, atom.quantifier)
    if atom.direction == AssetDirection.In:
        return Acquisition(atom.identifier, atom.quantifier)
    raise TypeError(f'Unrecognized atom.direction {atom.direction}')


def has_trans_transfer(asset_dirs) -> bool:
    dirs1, dirs2 = asset_dirs.values()
    return (AssetDirection.Out in dirs1 and AssetDirection.In in dirs2)\
        or (AssetDirection.In in dirs1 and AssetDirection.Out in dirs2)


def get_naive_trade(txid: str, atoms: list[Atom]) -> Effect:
    net_changes = defaultdict(lambda: Decimal(0))
    components = []
    for atom in atoms:
        net_changes[atom.identifier] += atom.quantifier\
            * atom.direction.value

    for asset, net_change in net_changes.items():
        if net_change > 0:
            components.append(
                Acquisition(asset, net_change)
            )
        elif net_change < 0:
            components.append(
                Disposal(asset, -net_change)
            )

    return Effect(
        Suggestion(Remainder.AssetChange, None),
        components,
        atoms[0].timestamp,
        txid,
        None,  # TODO: Attempt to get real ref from atom metadata
        None,
        'Unclassfied Trade'
    )


def effects_from_grouped_txns(grouped_txns: dict[str, list[Atom]]) -> Generator[Effect, None, None]:
    for txid, atoms in grouped_txns.items():
        asset_dirs = defaultdict(set)
        for atom in atoms:
            asset_dirs[atom.identifier].add(atom.direction)

        if len(asset_dirs) == 2 and has_trans_transfer(asset_dirs):
            yield get_naive_trade(txid, atoms)
        else:
            for i, atom in enumerate(atoms, start=1):
                asset_change = atom_to_asset_change(atom)

                if atom.purpose_hint == PurposeHint.TxFee:
                    rem = Remainder.TxFee
                    desc = 'Unclassified Transaction Fee Payment'
                elif isinstance(asset_change, Disposal):
                    rem = Remainder.Loss
                    desc = 'Unclassified Loss'
                elif isinstance(asset_change, Acquisition):
                    rem = Remainder.BaseIncome
                    desc = 'Unclassfied Income'
                else:
                    raise ValueError(
                        f'Could not assign naive remainder (atom: {atom})'
                    )

                yield Effect(
                    Suggestion(rem, None),
                    [asset_change],
                    atom.timestamp,
                    f'{txid}:{i}',
                    None,  # TODO: Attempt to get real ref from atom metadata,
                    None,
                    desc
                )


def naive_asset_flow(available_atoms: list[Atom], effects: list[Effect]) -> tuple[list[Atom], list[Effect]]:
    txns: dict[str, list[Atom]] = groupby(
        lambda a: a.txid,
        available_atoms
    )

    new_effects = effects + [*effects_from_grouped_txns(txns)]
    return [], new_effects
