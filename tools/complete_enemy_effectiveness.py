from reference_audit import *
E=load('enemies');count=0
for r in E:
 if not r.get('source_url'):continue
 c=doc(r['source_url']);res=' '.join(text(n) for n in sections(c,'Resistance'))
 for m in re.finditer(r'(Very Low|Very High|Low|Medium|High)\s+([^.;]+?)\s+Resistance',res,re.I):
  label=m[1].lower()
  for element in re.findall(r'\b(magic|fire|lightning|dark)\b',m[2],re.I):r['weaknesses'][element.lower()]='weak' if label in ['low','very low'] else 'resistant' if label in ['high','very high'] else 'neutral';count+=1
 for m in re.finditer(r'immune to\s+([^.;]+)',res,re.I):
  for status in re.findall(r'\b(poison|toxic|bleed|bleeding|petrification|petrify|curse)\b',m[1],re.I):r['status_effects'][{'bleeding':'bleed','petrification':'petrify'}.get(status.lower(),status.lower())]='immune'
save('enemies',E);print('Source-backed elemental effectiveness entries',count)
