import sys
from open_tax.collectors.default import AlchemyCollector
from open_tax.atomizers.default import AlchemyAtomizer
from open_tax.contextualizers.default import naive_asset_flow
from open_tax.contextualizers.base import Remainder
from open_tax.realizers.default import BasicRealizer
from dotenv import load_dotenv
import os
import json

from beancount.parser import printer


def main():
    load_dotenv()

    inp = json.loads(sys.argv[1])

    collector = AlchemyCollector(
        os.environ.get('ALCHEMY_KEY'),
        'https://eth-mainnet.g.alchemy.com/v2/',
        inp['wallets']
    )

    atomizer = AlchemyAtomizer()

    raw_alchemy_entries = collector.collect()
    print(json.dumps(raw_alchemy_entries, indent=2, default=repr))
    alchemy_atoms = atomizer.atomize(
        raw_alchemy_entries, {'chain': 'ethereum'})
    print(f'total atoms: {len(alchemy_atoms)}')

    leftover_atoms, effects = naive_asset_flow(alchemy_atoms, [])
    assert not leftover_atoms, 'Leftover Atoms'
    print(f'total effects: {len(effects)}')
    for e in effects:
        print(e)

    CURRENCY = inp['currency'].upper()

    bob = BasicRealizer('Assets:Cash', 'Assets:Crypto', {
        Remainder.AssetChange: 'Income:Asset-PnL',
        Remainder.BaseIncome: 'Income:Base',
        Remainder.TxFee: 'Expenses:Tx-Fees'
    }, CURRENCY)
    bean_txs = bob.realize(effects)

    fp = f'{inp["id"]}.beancount'
    with open(fp, 'w') as f:
        f.write('')

    with open(fp, 'a') as f:
        f.write(f'option "operating_currency" "{CURRENCY}"\n')
        printer.print_entries(bean_txs, file=f)


if __name__ == '__main__':
    try:
        main()
    except Exception as err:
        with open('error.txt', 'w') as f:
            f.write(repr(err) + '\n')
