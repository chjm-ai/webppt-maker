from pathlib import Path
import json
import tempfile
import argparse
from playwright.sync_api import sync_playwright
from PIL import Image,ImageDraw

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description='五页离线演示浏览器验收')
parser.add_argument('--html',type=Path,default=root/'output/demo.html')
parser.add_argument('--scratch',type=Path)
args=parser.parse_args()
scratch=args.scratch or Path(tempfile.mkdtemp(prefix='html-ppt-check-'))
scratch.mkdir(parents=True,exist_ok=True)
report={'errors':[],'external_requests':[],'slides':[],'checks':{}}
with sync_playwright() as p:
 browser=p.chromium.launch()
 context=browser.new_context(viewport={'width':1600,'height':1000},device_scale_factor=1)
 def block(route):
  report['external_requests'].append(route.request.url)
  route.abort()
 context.route('http://**/*',block)
 context.route('https://**/*',block)
 page=context.new_page()
 page.on('pageerror',lambda error:report['errors'].append(str(error)))
 page.goto(args.html.resolve().as_uri())
 page.wait_for_timeout(300)
 total=page.locator('.deck-page').count()
 report['pages']=total
 for i in range(total):
  page.evaluate('(n)=>deckPlayer.go(n)',i)
  info=page.locator('.deck-page.active .slide').evaluate('''s=>{
   const r=s.getBoundingClientRect(),cs=getComputedStyle(s),bad=[];
   for(const node of s.querySelectorAll('h1,h2,h3,p,span,figcaption,img')){
    const b=node.getBoundingClientRect();
    if(b.width&&b.height&&(b.left<r.left-2||b.top<r.top-2||b.right>r.right+2||b.bottom>r.bottom+2))bad.push({tag:node.tagName,text:node.textContent.slice(0,70),x:b.x,y:b.y,w:b.width,h:b.height});
   }
   return {id:s.dataset.slideId,layout:s.dataset.layout,ratio:r.width/r.height,background:cs.backgroundColor,titleSize:getComputedStyle(s.querySelector('h1,h2')).fontSize,images:[...s.querySelectorAll('img')].map(i=>({ok:i.complete&&i.naturalWidth>0,alt:i.alt})),overflow:bad};
  }''')
  report['slides'].append(info)
  page.locator('.deck-page.active .frame').screenshot(path=str(scratch/f'page-{i+1}.png'))
 page.evaluate('deckPlayer.go(0)');page.keyboard.press('ArrowRight')
 report['checks']['arrow_next']=page.evaluate('deckPlayer.current===1')
 page.keyboard.press('ArrowLeft');report['checks']['arrow_previous']=page.evaluate('deckPlayer.current===0')
 page.keyboard.press('ArrowLeft');report['checks']['lower_boundary']=page.evaluate('deckPlayer.current===0')
 page.keyboard.press('End');page.keyboard.press('ArrowRight');report['checks']['upper_boundary']=page.evaluate(f'deckPlayer.current==={total-1}')
 page.select_option('#jump','2');report['checks']['jump']=page.evaluate('deckPlayer.current===2')
 page.click('#overview');report['checks']['overview']=page.locator('.deck-page:visible').count()==total
 page.locator('.deck-page').nth(1).click();report['checks']['overview_select']=page.evaluate('deckPlayer.current===1&&!document.body.classList.contains("overview")')
 last=total-1
 page.click('#overview');page.locator('.deck-page').nth(last).focus();page.keyboard.press('Enter')
 report['checks']['overview_keyboard']=page.evaluate(f'deckPlayer.current==={last}&&!document.body.classList.contains("overview")')
 page.click('#fullscreen');page.wait_for_timeout(200)
 report['checks']['fullscreen']=page.evaluate('Boolean(document.fullscreenElement)')
 if report['checks']['fullscreen']:page.evaluate('document.exitFullscreen()')
 report['checks']['mobile']=[]
 for width,height in [(390,844),(844,390)]:
  page.set_viewport_size({'width':width,'height':height})
  for i in range(total):
   page.evaluate('(n)=>deckPlayer.go(n)',i)
   item=page.locator('.deck-page.active .frame').evaluate('e=>({ratio:e.clientWidth/e.clientHeight,width:innerWidth,scroll:document.body.scrollWidth})')
   item['page']=i+1;item['height']=height
   report['checks']['mobile'].append(item)
  page.locator('.deck-page.active .frame').screenshot(path=str(scratch/f'mobile-{width}.png'))
 page.evaluate('deckPlayer.go(1)')
 session=context.new_cdp_session(page)
 session.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':220,'y':120}]})
 session.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':90,'y':125}]})
 session.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
 report['checks']['touch_next']=page.evaluate('deckPlayer.current===2')
 page.evaluate('deckPlayer.go(NaN)');report['checks']['invalid_navigation']=page.evaluate('deckPlayer.current===2')
 browser.close()
contact=Image.new('RGB',(1440,1215),'#0e1115')
for i in range(total):
 image=Image.open(scratch/f'page-{i+1}.png').convert('RGB');image.thumbnail((720,405))
 contact.paste(image,((i%2)*720,(i//2)*405))
contact.save(scratch/'contact.jpg',quality=90)
(scratch/'browser-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))
print('CONTACT',scratch/'contact.jpg')

assert not report["errors"] and not report["external_requests"]
assert all(not p["overflow"] and all(i["ok"] for i in p["images"]) for p in report["slides"])
assert all(v for k,v in report["checks"].items() if k != "mobile")
assert all(p["width"] == p["scroll"] for p in report["checks"]["mobile"])
