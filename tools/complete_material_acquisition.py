from reference_audit import *
I=load('items');done=[]
for row in named_rows('/materials'):
 r=find(I,row['name'])
 if not r or r.get('obtaining'):continue
 c=doc(row['url']);nodes=sections(c,'Availability') or sections(c,'Location');words=' '.join(text(n) for n in nodes if n.name in ['p','ul','ol']).split()
 if not words:continue
 r['obtaining']=' '.join(words[:160]);r['acquisition_refs']=[{'name':n,'source_url':u} for node in nodes for n,u in list_pairs(node)];r['source_url']=row['url'];done.append(r['name'])
save('items',I);print('Filled acquisition information',len(done),done)
