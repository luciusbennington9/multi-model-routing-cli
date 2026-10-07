import argparse,json,os
CATALOG_URL=os.getenv('MODEL_CATALOG_URL','https://argolink.io/api/catalog/v1/catalog')
def choose(catalog,width,height,quality,budget):
 candidates=[]
 for item in catalog.get('models',[]):
  text=item.get('id','');pricing=item.get('pricing',{}).get('effective',{})
  if not any(x in text.lower() for x in ('nano-banana','gpt-image')):continue
  rate=pricing.get('image_2k') or pricing.get('2k') or pricing.get('image') 
  try: rate=float(rate)
  except (TypeError,ValueError):continue
  if rate<=budget:candidates.append((rate,text,item))
 if not candidates:raise ValueError('no catalog model meets budget')
 candidates.sort(key=lambda x:(0 if quality=='high' and 'pro' in x[1].lower() else 1,x[0]))
 return {'model':candidates[0][1],'estimated_usd':candidates[0][0],'width':width,'height':height,'quality':quality}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--catalog',required=True);ap.add_argument('--width',type=int,default=1024);ap.add_argument('--height',type=int,default=1024);ap.add_argument('--quality',choices=['low','medium','high'],default='medium');ap.add_argument('--budget',type=float,default=.05);ap.add_argument('--dry-run',action='store_true');a=ap.parse_args()
 out=choose(json.load(open(a.catalog)),a.width,a.height,a.quality,a.budget);print(json.dumps(out,indent=2))
if __name__=='__main__':main()
