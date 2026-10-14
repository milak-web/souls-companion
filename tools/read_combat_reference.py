import zipfile,xml.etree.ElementTree as E,json,pathlib,sys
sys.stdout.reconfigure(encoding='utf-8')
z=zipfile.ZipFile('audit/combat-reference.xlsx');ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
strings=[''.join(x.itertext()) for x in E.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si',ns)]
w=E.fromstring(z.read('xl/workbook.xml'));rels=E.fromstring(z.read('xl/_rels/workbook.xml.rels'));targets={x.attrib['Id']:x.attrib['Target'] for x in rels};sheets={}
for s in w.findall('m:sheets/m:sheet',ns):
 target=targets[s.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']];p=target.lstrip('/') if target.startswith('/') else 'xl/'+target;rows=[]
 for row in E.fromstring(z.read(p)).findall('m:sheetData/m:row',ns):
  d={}
  for c in row:
   v=c.find('m:v',ns);f=c.find('m:f',ns);val=v.text if v is not None else None
   if c.attrib.get('t')=='s' and val is not None:val=strings[int(val)]
   if val is not None or f is not None:d[c.attrib['r']]={'v':val,**({'f':f.text} if f is not None else {})}
  if d:rows.append(d)
 sheets[s.attrib['name']]=rows;print(s.attrib['name'],len(rows),str(rows[:2])[:1000])
pathlib.Path('audit/combat-reference-cells.json').write_text(json.dumps(sheets,ensure_ascii=False),encoding='utf-8')
