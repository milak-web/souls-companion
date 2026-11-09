"""Resolve the Fextralife enemy roster using its published name disambiguation."""
import argparse
import hashlib
import re
import urllib.parse
from pathlib import Path
from ds2_wiki_facts import body, rows, text, section_title
from enrich_ds2_wiki import read, write
from research_ds2_wiki import key
ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--cache',type=Path,required=True);args=parser.parse_args();cache=args.cache
    records=read(ROOT/'database/enemies.json');aliases=read(ROOT/'tools/ds2_entity_aliases.json')
    by_name={key(n):r for r in records for n in [r['name'],*r.get('aliases',[])]}
    titles={p['title'] for p in read(cache/'wiki-articles.json')}
    def article(title):return body((cache/(hashlib.sha256(title.encode()).hexdigest()[:20]+'.html')).read_bytes())
    changes=[]
    for table in article('Enemy Names Disambiguation').select('table'):
        for row in rows(table)[1:]:
            values=[text(c,False) for c in row]
            if len(values)!=3:continue
            official,guide,locations=values
            if official=='None':continue
            for name in guide.split(', '):
                r=by_name.get(key(name))
                if not r:continue
                r['aliases']=list(dict.fromkeys([*r.get('aliases',[]),official]))
                by_name[key(official)]=r
                if official in titles and r['name'] not in aliases:
                    aliases[r['name']]=official;changes.append({'id':r['id'],'title':official})
    write(ROOT/'database/enemies.json',records);write(ROOT/'tools/ds2_entity_aliases.json',aliases)
    for r in read(ROOT/'database/bosses.json')+read(ROOT/'database/npcs.json'):
        for n in [r['name'],*r.get('aliases',[])]:by_name.setdefault(key(n),r)
    roster=[]
    for a in article('Enemies').select('a[href]'):
        heading=section_title(a);name=text(a,False);href=a['href']
        if not re.fullmatch('[A-Z]',heading) or not name or not href.startswith('/') or name.startswith('Subcontent:'):continue
        match=by_name.get(key(name))
        # Shared aliases and qualified names are resolved by their entity URL.
        if not match:
            suffix=urllib.parse.unquote(href[1:]).replace('_',' ')
            match=by_name.get(key(suffix))
        roster.append({'wiki_name':name,'wiki_url':'https://darksouls2.wiki.fextralife.com'+href,'id':match['id'] if match else None})
    roster=list({r['wiki_url']:r for r in roster}.values())
    write(cache/'roster-audit.json',{'reference':'Enemy Names Disambiguation / Enemies','entries':roster,'alias_changes':changes})
    print('Published roster entries:',len(roster),'name matches:',sum(bool(r['id']) for r in roster),'alias updates:',len(changes))
    print('Unresolved:',[r['wiki_name'] for r in roster if not r['id']])

if __name__=='__main__':main()
