from open_tax.collectors.default import AlchemyCollector
from open_tax.atomizers.default import AlchemyAtomizer
from open_tax.contextualizers.default import naive_asset_flow
from open_tax.realizers.default import BasicRealizer
from dotenv import load_dotenv
import os
import json

load_dotenv()

collector = AlchemyCollector(
    os.environ.get('ALCHEMY_KEY'),
    'https://eth-mainnet.g.alchemy.com/v2/',
    ['0xf1a96Ce1cc0a5103Aeed21bCF89f83020f413Cb5']
)

atomizer = AlchemyAtomizer()

raw_alchemy_entries = collector.collect()
print(json.dumps(raw_alchemy_entries, indent=2, default=repr))
alchemy_atoms = atomizer.atomize(raw_alchemy_entries, {'chain': 'ethereum'})
print(f'total atoms: {len(alchemy_atoms)}')


leftover_atoms, effects = naive_asset_flow(alchemy_atoms, [])
assert not leftover_atoms, 'Leftover Atoms'
print(f'total effects: {len(effects)}')
for e in effects:
    print(e)

bob = BasicRealizer({}, 'EUR')
bean_txs = bob.realize(effects)
