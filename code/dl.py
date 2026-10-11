import json, requests, os, sys
from concurrent.futures import ThreadPoolExecutor
keep=json.load(open(sys.argv[1] if len(sys.argv)>1 else 'keep.json'))
def get(k):
    i=k[0]; f=os.path.join(sys.argv[2] if len(sys.argv)>2 else 'raw', f'{i}.json')
    if os.path.exists(f) and os.path.getsize(f)>100: return 1
    for t in range(3):
        try:
            r=requests.get(f'https://api.neotomadb.org/v2.0/data/downloads/{i}',timeout=120)
            if r.ok: open(f,'w').write(r.text); return 1
        except Exception as e: pass
    return 0
with ThreadPoolExecutor(16) as ex: res=list(ex.map(get,keep))
print(sum(res),len(res))
