"""Step 0b: download every Neotoma record in the dataset list through API v2 (one JSON file per dataset).
Usage: dl.py data/neotoma_dataset_list.json raw/      Existing files are skipped; failed downloads are listed."""
import json, os, sys
import requests
from concurrent.futures import ThreadPoolExecutor

LIST, RAW = sys.argv[1], sys.argv[2]
os.makedirs(RAW, exist_ok=True)
ids = [x[0] for x in json.load(open(LIST, encoding='utf-8'))]


def get(i):
    f = os.path.join(RAW, f'{i}.json')
    if os.path.exists(f) and os.path.getsize(f) > 100:
        return True
    for _ in range(3):
        try:
            r = requests.get(f'https://api.neotomadb.org/v2.0/data/downloads/{i}', timeout=120)
            if r.ok:
                open(f, 'wb').write(r.content)
                return True
        except requests.RequestException:
            pass
    return False


with ThreadPoolExecutor(16) as ex:
    ok = list(ex.map(get, ids))
failed = [i for i, o in zip(ids, ok) if not o]
print(f'{sum(ok)} of {len(ids)} records downloaded' + (f'; failed: {failed}' if failed else ''))
