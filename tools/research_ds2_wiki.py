"""Collect the public Fextralife DS2 wiki index and matched article sources.

Cached HTML is research input, never a deployable runtime dependency.
"""
import argparse
import concurrent.futures
import hashlib
import json
import re
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://darksouls2.wiki.fextralife.com'
CATALOGS = ['enemies', 'bosses', 'areas', 'weapons', 'items', 'magic', 'armor', 'npcs', 'covenants', 'articles']


def key(value):
    return re.sub(r'[^a-z0-9]+', '', unicodedata.normalize('NFKD', str(value)).encode('ascii', 'ignore').decode().lower())


def request(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'SoulsCompanionReferenceAudit/2.3 (public wiki research)'}), timeout=35).read()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cache', type=Path, default=ROOT / 'audit' / 'fextralife')
    parser.add_argument('--index-only', action='store_true')
    parser.add_argument('--workers', type=int, default=5)
    args = parser.parse_args()
    cache = args.cache
    cache.mkdir(parents=True, exist_ok=True)
    index_file = cache / 'wiki-articles.json'
    if index_file.exists():
        pages = json.loads(index_file.read_text(encoding='utf-8'))
    else:
        pages, continuation = [], {}
        while True:
            query = {'action': 'query', 'list': 'allpages', 'apnamespace': 0, 'aplimit': 500, 'apfilterredir': 'nonredirects', 'format': 'json', **continuation}
            data = json.loads(request(BASE + '/api.php?' + urllib.parse.urlencode(query)))
            pages.extend(data['query']['allpages'])
            print('Indexed', len(pages), 'wiki article titles', flush=True)
            if not data.get('continue'):
                break
            continuation = data['continue']
        index_file.write_text(json.dumps(pages, ensure_ascii=False, indent=2), encoding='utf-8')
    by_key = {}
    for page in pages:
        by_key.setdefault(key(page['title']), []).append(page)
    aliases = json.loads((ROOT / 'tools' / 'ds2_entity_aliases.json').read_text(encoding='utf-8'))
    records, unmatched = [], []
    for category in CATALOGS:
        source = ROOT / 'database' / (category + '.json')
        if not source.exists():
            continue
        for record in json.loads(source.read_text(encoding='utf-8-sig')):
            names = [aliases.get(record['name'], record['name']), record['name'], *record.get('aliases', [])]
            if record['name'] in aliases:
                names = [aliases[record['name']]]
            names += [re.sub(r'\s*\((?:weapon|shield|helm)\)$', '', record['name'], flags=re.I)]
            names += [re.sub(r'\s*\+\d+$', '', name) for name in names.copy()]
            if record['name'] not in aliases and record.get('source_url', '').startswith('https://darksouls2.wikidot.com/'):
                names.append(urllib.parse.unquote(record['source_url'].rsplit('/', 1)[-1]).replace('-', ' '))
            exact = {page['title']: page for page in pages}
            match = next((exact[name] for name in names if name in exact), None)
            match = match or next((by_key[key(name)][0] for name in names if len(by_key.get(key(name), [])) == 1), None)
            if match:
                records.append({'category': category, 'id': record['id'], 'name': record['name'], 'title': match['title'], 'pageid': match['pageid']})
            else:
                unmatched.append({'category': category, 'id': record['id'], 'name': record['name'], 'source': record.get('source_url')})
    # Category rosters and a few reference pages are also audited, even when not standalone app entries.
    reference_titles = ['Enemies', 'Bosses', 'Locations', 'Weapons', 'Shields', 'Armor', 'Items', 'Spells', 'Sorceries', 'Miracles', 'Hexes', 'Pyromancies', 'NPCs', 'Covenants', 'Consumables', 'Rings', 'Enemy Names Disambiguation', 'Parry', 'Backstabs']
    titles = sorted({record['title'] for record in records} | {by_key[key(title)][0]['title'] for title in reference_titles if len(by_key.get(key(title), [])) == 1})
    manifest = {'checked_on': '2026-10-16', 'wiki_articles': len(pages), 'records': records, 'unmatched': unmatched, 'sources': {}}
    manifest_file = cache / 'manifest.json'
    if manifest_file.exists():
        manifest['sources'] = json.loads(manifest_file.read_text(encoding='utf-8')).get('sources', {})
    manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Matched', len(records), 'catalog records to', len(titles), 'unique articles; unmatched', len(unmatched), flush=True)
    if args.index_only:
        return
    def fetch(title):
        url = BASE + '/' + urllib.parse.quote(title.replace(' ', '_'), safe='()_')
        file = cache / (hashlib.sha256(title.encode()).hexdigest()[:20] + '.html')
        if file.exists() and file.stat().st_size > 1000:
            return title, {'url': url, 'file': file.name, 'bytes': file.stat().st_size, 'status': 'cached'}
        for attempt in range(2):
            try:
                raw = request(url)
                if b'mw-parser-output' not in raw:
                    raise ValueError('Article body missing; response not imported')
                file.write_bytes(raw)
                return title, {'url': url, 'file': file.name, 'bytes': len(raw), 'status': 'downloaded'}
            except Exception as error:
                if attempt == 1:
                    return title, {'url': url, 'status': 'failed', 'error': str(error)}
                time.sleep(1.5)
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        for i, (title, result) in enumerate(pool.map(fetch, titles), 1):
            manifest['sources'][title] = result
            if i % 50 == 0:
                manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
                print('Collected', i, '/', len(titles), 'failed', sum(item['status'] == 'failed' for item in manifest['sources'].values()), flush=True)
    manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Collection complete:', len(manifest['sources']), 'articles;', sum(item['status'] == 'failed' for item in manifest['sources'].values()), 'failed', flush=True)


if __name__ == '__main__':
    main()
