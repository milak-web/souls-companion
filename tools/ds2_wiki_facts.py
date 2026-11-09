"""Mechanical reference extraction shared by the DS2 research import and checks."""
import re
import urllib.parse
from bs4 import BeautifulSoup, NavigableString, Comment

CHANNELS = ['standard', 'strike', 'slash', 'thrust', 'magic', 'fire', 'lightning', 'dark', 'poison', 'bleed', 'petrify', 'curse']


def clean(value):
    return re.sub(r'\s+', ' ', str(value)).strip().replace('\ufffd', '')


def text(node, icons=True):
    if node is None: return ''
    if not hasattr(node, 'descendants'): return clean(node)
    parts = []
    for item in node.descendants:
        if isinstance(item, NavigableString):
            if isinstance(item,Comment):continue
            if not item.find_parent(['script','style','sup']): parts.append(str(item))
        elif item.name == 'br': parts.append('; ')
        elif item.name == 'img' and icons: parts.append(item.get('title') or item.get('alt',''))
    return clean(' '.join(parts))


def body(raw, site='fex'):
    doc = BeautifulSoup(raw, 'html.parser')
    article = doc.select_one('.mw-parser-output') if site == 'fex' else doc.select_one('#page-content')
    if article is None:
        return None
    for unwanted in article.select('script,style,.toc,.navbox,.fex-category-list,.mw-editsection'):
        unwanted.decompose()
    heading=''
    for node in article.descendants:
        if not getattr(node,'name',None):continue
        node.attrs['data-reference-heading']=heading
        if node.name in ['h1','h2','h3','h4']:heading=text(node,False).replace(' | Dark Souls 2 Wiki','')
    return article


def rows(table):
    # Ignore nested table rows. Keep actual cells rather than expanding decorative colspans.
    return [row.find_all(['td','th'], recursive=False) for row in table.select('tr') if row.find_parent('table') == table]


def section_title(node):
    if node.has_attr('data-reference-heading'):return node['data-reference-heading']
    heading = node.find_previous(['h1', 'h2', 'h3', 'h4'])
    return text(heading, False).replace(' | Dark Souls 2 Wiki', '') if heading else ''


def variant(table, fallback):
    tab = table.find_parent(id=re.compile(r'^wiki-tab-\d+-\d+$'))
    if tab:
        labels = tab.find_parent(class_='yui-navset').select('.yui-nav li')
        i = int(tab['id'].rsplit('-', 1)[-1])
        if i < len(labels):
            return text(labels[i], False)
    heading=section_title(table)
    preceding=table.find_previous('table')
    if preceding:
        prior=rows(preceding)
        if len(prior)==1 and len(prior[0])==1:
            label=text(prior[0][0],False)
            if 0<len(label)<65:return label
    if heading.lower() in ['location','general','statistics','stats']:
        previous=table.find_previous(['strong','b'])
        if previous:
            label=text(previous,False).strip(': ')
            if 0<len(label)<65 and not label.lower().startswith(('bonfire','ng','note')):return label
    return heading or fallback


def numeric(value):
    return bool(re.fullmatch(r'[~\s]*\d[\d,]*(?:\.\d+)?(?:\s*[–-]\s*\d[\d,]*)?', str(value).strip()))


def cycles(value):
    """Read NG/NG+/NG+7 labels without inventing intermediate game cycles."""
    result = {}
    pattern = r'\bNG\s*(\+\s*\d*|)?\s*(?::|[–\-]|\s)\s*([~\d][\d,~. ]*)'
    for match in re.finditer(pattern, value, re.I):
        cycle = int(re.sub(r'\D', '', match[1])) if match[1] and re.search(r'\d', match[1]) else 1 if match[1] else 0
        raw = match[2].strip(' ,;.')
        if numeric(raw): result[cycle] = raw
    if not result and numeric(value): result[0] = value
    if not result:
        approximate=re.sub(r'^approx(?:imately)?[. ]*','~',value.strip(),flags=re.I)
        if numeric(approximate):result[0]=approximate
    if not result and '|' in value:
        pieces=value.split('|')
        if numeric(pieces[0].strip()):result[0]=pieces[0].strip()
        for piece in pieces[1:]:
            match=re.search(r'([\d,]+)\s*\(NG\+(\d*)\)',piece,re.I)
            if match:result[int(match[2] or '1')]=match[1]
    return result


def effect(value):
    value = value.lower().strip()
    if re.search(r'immune|no effect|ineffective', value): return 'immune'
    if re.search(r'very low|\bweak\b|vulnerable', value): return 'weak'
    if re.search(r'\blow\b', value): return 'weak'
    if re.search(r'\bhigh\b|resist', value): return 'resistant'
    if re.search(r'normal|medium|neutral', value): return 'neutral'
    if re.search(r'susceptible|effective|\byes\b', value): return 'susceptible'


def canonical_channel(value):
    value = value.lower().replace('_',' ').replace('-',' ')
    if 'bleed' in value: return 'bleed'
    if 'petrif' in value: return 'petrify'
    return next((channel for channel in CHANNELS if re.search(r'\b' + channel + r'\b', value)), None)


def criticals(article):
    output = {}
    # Only passive or explicit player-action wording is accepted. An enemy backstabbing
    # the player does not establish that the enemy can itself be backstabbed.
    for field, root in [('can_parry', r'parr(?:y|ied|iable|yable)'), ('can_backstab', r'backstab(?:bed|bing|s)?')]:
        evidence = []
        for node in article.select('p,li,td'):
            value = text(node, False)
            if len(value) > 2500 or not re.search(root, value, re.I): continue
            negatives = [r'(?:cannot|can not|can\'t|can’t|not able to)\s+(?:be\s+)?(?:\w+[ ,]+){0,4}' + root,
                         r'(?:immune|immunity)\s+to\s+(?:\w+\s+){0,2}' + root,
                         r'(?:cannot|can\'t|can’t)\s+be\s+[^.!?;]{0,65}' + root,
                         r'(?:unparryable|unparriable)' if field == 'can_parry' else r'backstab[- ]immune']
            if field=='can_backstab':negatives.append(r'protects?\s+[^.!?;]{0,40}from\s+backstab')
            positive = [r'(?:can|may)\s+(?:also\s+|easily\s+|still\s+|actually\s+)?be\s+(?:blocked\s*[/,]\s*)?' + root,
                        r'can be blocked/?\s*' + root,
                        r'(?:can|may)\s+(?:also\s+)?be\s+(?:\w+\s+){0,3}' + root,
                        r'(?:easy|easily)\s+(?:to\s+|be\s+)?' + root]
            if field == 'can_backstab':
                positive += [r'(?:with|for|using)\s+(?:a\s+)?backstab', r'(?:rolling and|roll and|by|try|easy to|simply)\s+backstabb', r'backstab\s+(?:them|him|her|it|the enemy)', r'(?:vulnerable|susceptible) to backstab',r'backstabs? (?:are|is) (?:very |highly )?effective']
                positive += [r'(?:easy|great) to (?:\w+\s+){0,3}backstab',r'vulnerable to (?:\w+[ ,]+){0,3}backstab',r'(?:their|its|his) inv[ia]n[ic]*b?ility after [^.!?;]{0,30}backstab']
            else:positive += [r'(?:large|long|easy|generous) parry windows?']
            if any(re.search(pattern, value, re.I) for pattern in negatives): evidence.append((False, value))
            elif any(re.search(pattern, value, re.I) for pattern in positive): evidence.append((True, value))
        # Conflicting prose needs manual review; do not decide by keyword frequency.
        values = {value for value, _ in evidence}
        if len(values) == 1:
            output[field] = {'value': evidence[0][0], 'evidence': evidence[0][1]}
            if field=='can_backstab' and not evidence[0][0] and 'crystallized' in evidence[0][1].lower():
                output[field].update({'value':True,'conditional':True,'condition':'Regular form only; crystallized enemies cannot be backstabbed.'})
        elif values:
            output[field] = {'value': True, 'evidence': '\n'.join(value for _, value in evidence), 'conditional': True}
            if field=='can_backstab' and any('ghost form' in value.lower() for _,value in evidence):output[field]['condition']='Corporeal form only; ghost-form enemies cannot be backstabbed.'
    table_values=[]
    for table in article.select('table'):
        data=rows(table)
        for i,row in enumerate(data[:4]):
            headers=[text(cell,False).lower() for cell in row]
            index=next((j for j,value in enumerate(headers) if re.fullmatch(r'parr(?:y|i)able[?*; ]*|can be parried[?; ]*',value)),None)
            if index is None:continue
            for following in data[i+1:]:
                if len(following)!=len(headers):continue
                value=text(following[index],False).lower().strip('; ')
                if value in ['yes','no']:table_values.append(value=='yes')
            break
    if table_values:
        output['can_parry']={'value':any(table_values),'evidence':'Attack table: '+', '.join('Yes' if value else 'No' for value in table_values),'conditional':len(set(table_values))>1}
    return output


def wikidot_enemy(article, name, url):
    output = {'profiles': [], 'weaknesses': {}, 'status_effects': {}, 'modifiers': [], 'criticals': criticals(article), 'source': url}
    for table in article.select('table'):
        cells = rows(table)
        if not cells: continue
        context = variant(table, name)
        header = None
        for row in cells:
            values = [text(cell, False) for cell in row]
            labels=[text(cell).lower().removesuffix('.png') for cell in row]
            normalized = ['hp' if value in ['health','hp'] else value for value in labels]
            if {'hp', 'souls'}.issubset(normalized):
                if any(label in normalized for label in ['new game','ng','intensity','bonfire intensity']):
                    header = normalized
                    continue
            if header and len(values) == len(header):
                cycle_key = next(key for key in ['new game','ng','intensity','bonfire intensity'] if key in header)
                cycle = values[header.index(cycle_key)]
                hp, souls = values[header.index('hp')], values[header.index('souls')]
                number=re.match(r'^\d+',cycle)
                if number and (numeric(hp) or numeric(souls)):
                    if hp in ['0','0.0'] and souls in ['0','0.0']:continue
                    cycle = int(number[0]) - (0 if cycle_key in ['new game','ng'] else 1)
                    output['profiles'].append({'context':context,'cycle':cycle,'intensity':str(cycle + 1),'hp':hp if numeric(hp) else None,'souls':souls if numeric(souls) else None,'source':url,'reference':'Wikidot'})
            if len(values) in [2,3]:
                channel = canonical_channel(text(row[0]))
                status = effect(values[1])
                if channel and status:
                    output['status_effects' if channel in ['poison','bleed','petrify','curse'] else 'weaknesses'][channel] = status
                if channel and re.fullmatch(r'~?\d+(?:\.\d+)?%',values[1]):
                    kind='Physical damage multiplier' if channel in ['strike','thrust','slash','standard'] else 'Elemental resistance'
                    output['modifiers'].append({'channel':channel,'value':values[1],'kind':kind,'source':url})
                    if kind=='Physical damage multiplier':
                        multiplier=float(values[1].strip('~%'))
                        output['weaknesses'][channel]='weak' if multiplier>100 else 'resistant' if multiplier<100 else 'neutral'
    for node in article.select('li,p'):
        heading=section_title(node)
        value=text(node,False)
        if re.search(r'resistan',heading,re.I):
            match=re.match(r'^(Very Low|Low|Medium|High|Very High)\s+(.+?)\s+Resistance',value,re.I)
            if match:
                state={'very low':'weak','low':'weak','medium':'neutral','high':'resistant','very high':'resistant'}[match[1].lower()]
                for channel in ['magic','fire','lightning','dark']:
                    if re.search(r'\b'+channel+r'\b',match[2],re.I):output['weaknesses'][channel]=state
        if re.search(r'effectiveness|weakness',heading,re.I):
            match=re.match(r'(Strike|Thrust|Slash)\s*:\s*(~?\d+(?:\.\d+)?%)',value,re.I)
            if match:
                output['modifiers'].append({'channel':match[1].lower(),'value':match[2],'kind':'Physical damage multiplier','source':url})
                multiplier=float(match[2].strip('~%'))
                output['weaknesses'][match[1].lower()]='weak' if multiplier>100 else 'resistant' if multiplier<100 else 'neutral'
    output['modifiers']=list({(m['channel'],m['value'],m['kind']):m for m in output['modifiers']}.values())
    return output


def fex_enemy(article, name, url):
    output = {'profiles': [], 'weaknesses': {}, 'status_effects': {}, 'criticals': criticals(article), 'source': url, 'attacks': [], 'facts': []}
    tables = article.select('table')
    for index, table in enumerate(tables):
        context = variant(table, name)
        values_by_label = {}
        for row in rows(table):
            values = [text(cell, False) for cell in row]
            if len(values) == 2 and values[0] and len(values[0]) < 55:
                values_by_label[values[0].lower().strip('?; :')] = values[1].strip('; ')
        if index == 0:
            for label, status in [('weakness','weak'), ('weak','weak'), ('resistance','resistant'), ('resists','resistant')]:
                for channel in CHANNELS:
                    if channel in values_by_label.get(label, '').lower():
                        output['status_effects' if channel in ['poison','bleed','petrify','curse'] else 'weaknesses'][channel] = status
            output['respawn'] = values_by_label.get('respawns')
            for label in ['immune','immunity']:
                for channel in CHANNELS:
                    if channel in values_by_label.get(label,'').lower():output['status_effects' if channel in ['poison','bleed','petrify','curse'] else 'weaknesses'][channel]='immune'
        hp_by_cycle = cycles(values_by_label.get('hp', ''))
        if not hp_by_cycle:
            table_rows = rows(table)
            for row_number, row in enumerate(table_rows):
                headings = [re.sub(r'^icon\s*', '', text(cell).lower().strip('; ?: ')) for cell in row]
                headings = ['hp' if value == 'health' else value for value in headings]
                if 'hp' in headings and row_number + 1 < len(table_rows):
                    next_values = [text(cell, False) for cell in table_rows[row_number + 1]]
                    if len(next_values) == len(headings):
                        hp_value = next_values[headings.index('hp')].strip('; ')
                        hp_by_cycle = cycles(hp_value)
                        if 'location' in headings:
                            context += ' · ' + next_values[headings.index('location')]
                        if 'ng' in headings:
                            game = next_values[headings.index('ng')].strip('; ')
                            game_cycle = 0 if game == 'NG' else 1 if game == 'NG+' else int(game[3:]) if re.fullmatch(r'NG\+\d+', game) else 0
                            if numeric(hp_value): hp_by_cycle = {game_cycle:hp_value}
                        if 'souls' in headings:
                            values_by_label['souls'] = next_values[headings.index('souls')].strip('; ')
        if hp_by_cycle:
            # Soul rewards are often in a separate Drops list below this variant table.
            rewards = cycles(values_by_label.get('souls',''))
            node = table
            while node:
                node = node.find_next()
                if not node or (node.name == 'table' and node is not table): break
                if node.name in ['p','li']:
                    value = text(node, False)
                    match = re.search(r'\bSouls\s*:\s*(.*)', value, re.I)
                    if not match and re.search(r'drop',section_title(node),re.I) and re.search(r'\bsouls\b',value,re.I):
                        rewards.update(cycles(value))
                        if rewards:break
                    if match:
                        rewards.update(cycles(match[1]))
                        for sibling in node.find_next_siblings('li', limit=3): rewards.update(cycles(text(sibling, False)))
                        if rewards: break
            for cycle, hp in hp_by_cycle.items():
                output['profiles'].append({'context':context,'cycle':cycle,'intensity':str(cycle+1),'hp':hp,'souls':rewards.get(cycle),'source':url,'reference':'Fextralife'})
    # Sources sometimes publish a reward even when they omit HP entirely.
    for node in article.select('li,p'):
        value=text(node,False)
        if not re.search(r'drop',section_title(node),re.I) or not re.search(r'\bsouls\b',value,re.I):continue
        for cycle,reward in cycles(value).items():
            if not any(p['cycle']==cycle and p.get('souls') for p in output['profiles']):
                output['profiles'].append({'context':name,'cycle':cycle,'intensity':str(cycle+1),'hp':None,'souls':reward,'source':url,'reference':'Fextralife'})
    for label, state in [('poison','poison'),('bleed','bleed'),('toxic','toxic')]:
        if re.search(r'immune to\s+(?:\w+[ ,]+){0,3}'+label, text(article, False), re.I): output['status_effects'][state] = 'immune'
    return output


def reference_facts(article):
    """Compact mechanical tables; do not mirror descriptions, lore or upgrade tables."""
    output = []
    for table in article.select('table'):
        if table.find_parent('table'): continue
        heading = section_title(table)
        if re.search(r'upgrad|reinforce|infus|moveset|move set|attack|lore|description|strategy|notes', heading, re.I): continue
        table_rows = rows(table)
        if any(len(row)>1 and all(cell.name=='th' for cell in row) for row in table_rows[:3]): continue
        if any({'hp','souls'}.issubset({text(cell).lower().replace('icon ','').strip('; ') for cell in row}) for row in table_rows[:4]):continue
        facts = []
        for row in table_rows:
            if row and all(cell.name == 'th' for cell in row): continue
            values = [text(cell) for cell in row]
            if len(values) in [2,4] and all(len(value)<350 for value in values):
                for i in range(0,len(values),2):
                    label, value = values[i:i+2]
                    if row[i+1].find('img'):continue
                    if 0 < len(label) < 65 and value and not re.search(r'\b(?:Soulslike|Wiki|Build|Description|Lore)\b', label, re.I):
                        if re.fullmatch(r'[\d\s.,+–/-]+', label): continue
                        if re.match(r'^\d|^[*; ()SABCDE+-]+$',label):continue
                        if len(value.split()) > 23: continue
                        facts.append({'label':label,'value':value})
        if facts:
            output.append({'heading':heading or 'Reference properties','facts':facts[:24]})
    return output


def reference_tables(article):
    output=[]
    for table in article.select('table'):
        if table.find_parent('table'): continue
        heading=section_title(table)
        if re.search(r'upgrad|reinforce|infus|move.?set|attack|lore|description|strategy|table key',heading,re.I):continue
        data=rows(table)
        for i,row in enumerate(data[:3]):
            if len(row)<2 or not all(cell.name=='th' for cell in row):continue
            headers=[text(cell) for cell in row]
            if len(headers)>12 or any(len(h)>70 for h in headers):continue
            values=[]
            for following in data[i+1:]:
                if len(following)!=len(headers) or all(cell.name=='th' for cell in following):continue
                cells=[text(cell,False) for cell in following]
                if any(len(c.split())>23 for c in cells):continue
                values.append(cells)
            if values:output.append({'heading':heading or 'Reference table','headers':headers,'rows':values[:150]})
            break
    return output


def section_links(article, keywords, base='https://darksouls2.wiki.fextralife.com'):
    output = []
    for anchor in article.select('a[href]'):
        href = anchor['href']
        if not href.startswith('/') or href.startswith('//') or href.startswith('/File:') or 'index.php?' in href: continue
        heading = section_title(anchor).lower()
        if any(keyword in heading for keyword in keywords):
            if keywords==['drops']:
                parent=anchor.find_parent(['li','p'])
                if parent and re.search(r'(?:does? not|doesn.t|cannot|can.t|never)\s+(?:be\s+)?(?:\w+\s+){0,2}drop',text(parent,False),re.I):continue
            name = text(anchor, False)
            if name: output.append({'name':name,'source_url':base+href.split('#')[0]})
    return list({(row['name'],row['source_url']):row for row in output}.values())
