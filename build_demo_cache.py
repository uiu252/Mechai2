"""Rebuild the bundled deterministic demo fixture from the actual workbook."""
import json
from agents import CACHE, offline_perspective
from data_loader import load_products, fingerprint
from schemas import ROLES

def main():
    products = load_products()
    cache = {'schema_version':1, 'assortment_fingerprint':fingerprint(products),
        'provenance':'Prepared, deterministic demo outputs generated from the bundled workbook. These are not prior live API responses.',
        'analyses':{role:offline_perspective(products,role).model_dump() for role in ROLES}}
    CACHE.write_text(json.dumps(cache,indent=2,ensure_ascii=False),encoding='utf-8')
    print(f'Cached {len(cache["analyses"])} perspectives for {len(products)} actual workbook products.')

if __name__ == '__main__': main()
