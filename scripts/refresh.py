#!/usr/bin/env python3
"""Fetch real NRCan CSVs and atomically publish a validated, year-sharded snapshot."""
import csv,hashlib,io,json,math,re,shutil,tempfile,time
from datetime import datetime,timezone
from pathlib import Path
from urllib.error import HTTPError,URLError
from urllib.parse import urlsplit
from urllib.request import Request,urlopen
ROOT=Path(__file__).resolve().parents[1]
UA='CoolCode CarBench/1.0 (+https://coolcode.ca/carbench/; public data)'

def download(url):
 p=urlsplit(url)
 if p.scheme!='https' or p.hostname!='open.canada.ca':raise ValueError('Unexpected source host')
 for attempt in range(3):
  try:
   with urlopen(Request(url,headers={'User-Agent':UA,'Accept':'application/json,text/csv,*/*'}),timeout=75) as r:
    data=r.read(15000001)
    if len(data)>15000000:raise ValueError('Source exceeds size limit')
    return data
  except (HTTPError,URLError,TimeoutError) as e:
   if isinstance(e,HTTPError) and e.code not in (429,500,502,503,504):raise
   if attempt==2:raise
   time.sleep(3*(attempt+1))

def num(value,required=False):
 try:n=float(value)
 except (ValueError,TypeError):
  if required:raise ValueError('Missing consumption value')
  return None
 if not math.isfinite(n) or n<0:raise ValueError('Invalid consumption value')
 return n

def parse_csv(data,kind,source):
 try:text=data.decode('utf-8-sig')
 except UnicodeDecodeError:text=data.decode('cp1252')
 reader=csv.DictReader(io.StringIO(text));headers={h.strip() for h in reader.fieldnames or []}
 if not {'Model year','Make','Model','Vehicle class'}<=headers:raise ValueError('CSV schema changed')
 out=[]
 for raw in reader:
  r={k.strip():v.strip() for k,v in raw.items() if k and v is not None}
  if not r.get('Model year','').isdigit():continue
  year=int(r['Model year'])
  if not 1995<=year<=2100:raise ValueError('Unexpected model year')
  fuel=r.get('Fuel type 2',r.get('Fuel type',''))
  city=num(r.get('City (L/100 km)')) if kind!='electric' else None
  highway=num(r.get('Highway (L/100 km)')) if kind!='electric' else None
  combined=num(r.get('Combined (L/100 km)'),kind!='electric') if kind!='electric' else None
  electric=num(r.get('Combined (kWh/100 km)'),kind=='electric') if kind=='electric' else None
  modeFuel=0
  modeText=r.get('Combined Le/100 km','')
  if kind=='plugin':
   match=re.search(r'([\d.]+)\s*kWh',modeText)
   if not match:raise ValueError('Cannot parse plug-in electric-mode use')
   electric=num(match[1],True)
   match=re.search(r'\+\s*([\d.]+)\s*L',modeText)
   modeFuel=num(match[1],True) if match else 0
  identity='|'.join([str(year),r['Make'],r['Model'],r.get('Engine size (L)',''),r.get('Transmission',''),fuel,kind,str(combined),str(electric),str(modeFuel)])
  out.append({'id':hashlib.sha256(identity.encode()).hexdigest()[:16],'year':year,'make':r['Make'],'model':r['Model'],'class':r['Vehicle class'],'kind':kind,'fuel':fuel,'engine':r.get('Engine size (L)',''),'transmission':r.get('Transmission',''),'city':city,'highway':highway,'combined':combined,'electric':electric,'modeFuel':modeFuel,'range':num(r.get('Range (km)',r.get('Range 1 (km)'))),'source':source,'modeText':modeText})
 if not out:raise ValueError('No vehicle rows')
 return out

def main():
 conf=json.loads((ROOT/'config/sources.json').read_text());catalogue=json.loads(download(conf['catalogue']))
 if catalogue.get('success') is not True:raise ValueError('Catalogue rejected request')
 resources={r['id']:r for r in catalogue['result']['resources']};records={};sources=[]
 for spec in conf['resources']:
  r=resources[spec['id']]
  if r.get('format')!='CSV' or 'en' not in r.get('language',[]):raise ValueError('Resource language or format changed')
  body=download(r['url']);rows=parse_csv(body,spec['kind'],len(sources))
  if len(rows)<conf['minimumPerResource']:raise ValueError('Unexpectedly small source')
  sources.append({'id':r['id'],'title':r['name'],'url':r['url'],'updated':r.get('last_modified'),'sha256':hashlib.sha256(body).hexdigest(),'rows':len(rows)})
  records.update({row['id']:row for row in rows});time.sleep(1)
 if len(records)<conf['minimumVehicles']:raise ValueError('Incomplete capture')
 years=sorted({r['year'] for r in records.values()},reverse=True)
 manifest={'capturedAt':datetime.now(timezone.utc).isoformat(),'dataset':conf['dataset'],'licence':'https://open.canada.ca/en/open-government-licence-canada','sources':sources,'count':len(records),'years':[{'year':y,'count':sum(r['year']==y for r in records.values())} for y in years]}
 target=ROOT/'web/data'
 with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
  stage=Path(tmp)/'data';stage.mkdir()
  (stage/'index.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
  for y in years:
   rows=sorted([r for r in records.values() if r['year']==y],key=lambda r:(r['make'],r['model'],r['id']))
   (stage/f'vehicles-{y}.json').write_text(json.dumps(rows,separators=(',',':'),ensure_ascii=False)+'\n')
  if target.exists():shutil.rmtree(target)
  shutil.copytree(stage,target)
 print(f'Captured {len(records)} vehicles from {len(sources)} sources; years {min(years)}–{max(years)}')
if __name__=='__main__':main()
