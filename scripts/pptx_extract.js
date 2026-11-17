/* 只消费本 skill 的最终 DOM；坐标统一到固定画布，不推测原始设计。 */
(() => {
  const W = 1600, H = 900;
  let serial = 0;
  const number = value => parseFloat(value) || 0;
  const generated = s => !['none', 'normal', '""', "''"].includes(s.content) ||
    (s.content === '""' && (s.backgroundImage !== 'none' || number(s.width) || number(s.height)));

  window.pptxPrepare = () => {
    const pages = [...document.querySelectorAll('main.deck > section.deck-page')];
    if (!pages.length || pages.some(p => p.querySelectorAll(':scope > .frame > article.slide[data-slide-id][data-layout]').length !== 1))
      throw new Error('不符合本 skill 的 deck-page/frame/article.slide 契约');
    const ids = pages.map(p => p.querySelector('.slide').dataset.slideId);
    if (new Set(ids).size !== ids.length) throw new Error('页面 ID 重复');
    document.body.classList.remove('overview', 'editing');
    document.querySelectorAll('[contenteditable]').forEach(e => e.removeAttribute('contenteditable'));
    document.querySelectorAll('video,audio').forEach(e => e.pause());
    const style = document.createElement('style');
    style.textContent = `
      html,body {margin:0!important;padding:0!important;width:${W}px!important;height:${H}px!important;overflow:hidden!important;background:transparent!important}
      .player-controls,.player-message,.notes-panel {display:none!important}
      main.deck {display:block!important;padding:0!important;margin:0!important;width:${W}px!important;min-height:0!important}
      main.deck > .deck-page {display:none!important;width:${W}px!important;margin:0!important}
      main.deck > .deck-page[data-pptx-active] {display:block!important}
      .deck-page > .frame {width:${W}px!important;height:${H}px!important;aspect-ratio:auto!important}
      *,*::before,*::after {animation:none!important;transition:none!important;caret-color:transparent!important}
      [data-player-editable] {outline:none!important}
    `;
    document.head.append(style);
    return pages.length;
  };

  window.pptxActivate = async index => {
    const pages = [...document.querySelectorAll('main.deck > section.deck-page')];
    pages.forEach((p,i) => {
      p.toggleAttribute('data-pptx-active', i === index);
      p.inert = false;
      p.removeAttribute('aria-hidden');
    });
    window.scrollTo(0,0);
    const timeout = new Promise((_,bad) => setTimeout(() => bad(new Error('字体/图片加载超过 10 秒')),10000));
    await Promise.race([document.fonts.ready, timeout]);
    const slide = pages[index].querySelector('.slide');
    await Promise.race([Promise.all([...slide.querySelectorAll('img')].map(async img => {
      if (!img.complete) await new Promise((ok, bad) => {img.onload=ok;img.onerror=bad;});
      if (!img.naturalWidth) throw new Error('图片加载失败');
      await img.decode();
    })), timeout]);
    // CSS 背景/蒙版也可能承载图形，不能只等 <img>。
    const urls=new Set();
    for(const el of [slide,...slide.querySelectorAll('*')]) {
      for(const pseudo of [null,'::before','::after']) {
        const computed=getComputedStyle(el,pseudo);
        for(const value of [computed.backgroundImage,computed.maskImage]) {
          for(const match of value.matchAll(/url\((?:"([^"]*)"|'([^']*)'|([^)]*))\)/g)) urls.add(match[1]||match[2]||match[3]);
        }
      }
    }
    await Promise.race([Promise.all([...urls].map(async url=>{
      if(!url.startsWith('data:')) {
        window.__pptxCsp?.push({url:url.slice(0,300),type:'self-contained-css-image'});
        throw new Error('CSS 图片不是内嵌 data: 资源');
      }
      const img=new Image(); img.src=url; await img.decode();
    })),timeout]);
    await new Promise(ok => requestAnimationFrame(() => requestAnimationFrame(ok)));
    return slide.dataset.slideId;
  };

  function matrix(s) {
    if (s.transform === 'none') return {a:1,b:0,c:0,d:1};
    return new DOMMatrix(s.transform);
  }

  function complex(s, el, isSlide=false) {
    const m = matrix(s);
    if (!m.is2D && s.transform !== 'none') return '3D transform';
    if (Math.abs(m.b) > .0001 || Math.abs(m.c) > .0001 || m.a <= 0 || m.d <= 0) return 'rotation/skew/reflection';
    const independentScale=(s.scale||'none').split(' ').map(number);
    if (el.textContent.trim() && (Math.abs(m.a-m.d)>.001 ||
        (independentScale.length>1 && Math.abs(independentScale[0]-independentScale[1])>.001))) return 'nonuniform text scale';
    if (s.rotate && s.rotate !== 'none' && s.rotate !== '0deg') return 'individual rotate';
    if (s.filter !== 'none' || s.backdropFilter !== 'none') return 'filter/backdrop-filter';
    if (s.clipPath !== 'none' || s.maskImage !== 'none') return 'clip-path/mask';
    if (s.mixBlendMode !== 'normal') return 'mix-blend-mode';
    // CSS opacity 合成整组；逐对象分摊 alpha 会改变重叠区域颜色。
    if (number(s.opacity) < 1) return 'group opacity';
    if (s.writingMode !== 'horizontal-tb' || s.direction !== 'ltr') return 'vertical/RTL text';
    if (s.textShadow !== 'none' || s.webkitTextStrokeWidth !== '0px' || s.backgroundClip === 'text' || s.webkitTextFillColor !== s.color) return 'text effect';
    if (!['none','uppercase','lowercase'].includes(s.textTransform)) return 'text transform';
    if (s.perspective !== 'none') return 'perspective';
    if (['SVG','CANVAS','MATH','VIDEO','IFRAME','OBJECT','EMBED','INPUT','TEXTAREA','SELECT'].includes(el.tagName.toUpperCase())) return el.tagName.toLowerCase();
    if (!isSlide && ['hidden','clip','scroll','auto'].includes(s.overflowX) && el.scrollWidth > el.clientWidth + 1) return 'horizontal clipping';
    if (!isSlide && ['hidden','clip','scroll','auto'].includes(s.overflowY) && el.scrollHeight > el.clientHeight + 1) return 'vertical clipping';
    return null;
  }

  function rasterTextChars(el) {
    let count=0;
    const walker=document.createTreeWalker(el,NodeFilter.SHOW_TEXT);
    const range=document.createRange();
    while(walker.nextNode()) {
      const node=walker.currentNode;
      if(node.parentElement.closest('script,style,metadata,title,desc')) continue;
      const st=getComputedStyle(node.parentElement);
      range.selectNodeContents(node);
      const r=range.getBoundingClientRect();
      if(st.visibility==='visible' && r.width && r.height) count+=node.data.trim().length;
    }
    return count;
  }

  function decorations(el) {
    const lines = new Set();
    for (let node = el; node; node = node.parentElement) {
      const s = getComputedStyle(node);
      s.textDecorationLine.split(' ').forEach(line => lines.add(line));
      // 装饰不跨原子行内盒、浮动或脱离文档流的子树传播。
      if (['inline-block','inline-table','inline-flex','inline-grid'].includes(s.display) ||
          ['absolute','fixed'].includes(s.position) || s.cssFloat !== 'none') break;
    }
    return lines;
  }

  function font(s, sx, sy, opacity, decoration = new Set(s.textDecorationLine.split(' '))) {
    return {
      family:s.fontFamily.split(',')[0].trim().replace(/^["']|["']$/g,''),
      size:number(s.fontSize)*sy, bold:number(s.fontWeight)>=600, italic:s.fontStyle !== 'normal',
      color:s.color, opacity, underline:decoration.has('underline'),
      strike:decoration.has('line-through'), spacing:s.letterSpacing === 'normal' ? 0 : number(s.letterSpacing)*sx,
      scaleX:sx/sy, transform:s.textTransform
    };
  }

  function textLines(node, slideRect, scale, style, opacity) {
    const result = [], range = document.createRange();
    let line = null;
    // Range 按 Unicode 码点测量，避免切开代理对；保留浏览器决定的换行。
    for (let i=0; i<node.length;) {
      const char = String.fromCodePoint(node.data.codePointAt(i));
      range.setStart(node,i); range.setEnd(node,i+char.length); i += char.length;
      const r = range.getBoundingClientRect();
      if (!r.width || !r.height || (!node.data.trim() && !['pre','pre-wrap','break-spaces'].includes(style.whiteSpace))) continue;
      if (!line || Math.abs(line.top-r.top) > 1 || r.left < line.lastLeft-.5) {
        line = {text:'',top:r.top,lastLeft:r.left,x:r.left,y:r.top,w:0,h:r.height};
        result.push(line);
      }
      let value = char;
      if (!['pre','pre-wrap','break-spaces'].includes(style.whiteSpace) && /\s/u.test(value)) value=' ';
      line.text += value;
      line.w = Math.max(line.w,r.right-line.x);
      line.h = Math.max(line.h,r.height); line.lastLeft=r.left;
    }
    return result.filter(l => l.text.trim()).map(l => ({
      kind:'text', text:l.text,
      box:{x:(l.x-slideRect.x)/scale.x,y:(l.y-slideRect.y)/scale.y,w:l.w/scale.x,h:l.h/scale.y},
      font:font(style,1,1,opacity)
    }));
  }

  window.pptxExtract = () => {
    const slide = document.querySelector('[data-pptx-active] .slide');
    const root = slide.getBoundingClientRect();
    const s = getComputedStyle(slide);
    if (root.width < 1 || root.height < 1) throw new Error('页面不可见');
    const scale = {x:root.width/number(s.width),y:root.height/number(s.height)};
    // slide 必须填满 frame；将布局缩放反归一化后再换算成 1600×900。
    if (Math.abs(root.width/root.height-W/H) > .02) throw new Error('slide 不是 16:9');
    if (Math.abs(root.x)>.5 || Math.abs(root.y)>.5 || Math.abs(root.width-W)>1 || Math.abs(root.height-H)>1)
      throw new Error('slide 最终边界必须填满固定 frame（允许内部 CSS scale，不支持偏移/缩小整个页面）');
    const norm = {x:W/root.width,y:H/root.height};
    const elements = [], warnings = [];
    let visited = 0, chars = 0;
    const rect = el => {
      const r=el.getBoundingClientRect();
      return {x:(r.x-root.x)*norm.x,y:(r.y-root.y)*norm.y,w:r.width*norm.x,h:r.height*norm.y};
    };
    const key = el => {
      if (!el.hasAttribute('data-pptx-key')) el.setAttribute('data-pptx-key',String(++serial));
      return el.getAttribute('data-pptx-key');
    };
    const add = (el,item) => elements.push({...item,key:key(el),tag:el.tagName.toLowerCase()});
    function visit(el, inheritedOpacity=1) {
      if (++visited > 5000) throw new Error('超过 5000 元素上限');
      const st=getComputedStyle(el);
      if (st.display === 'none' || number(st.opacity) === 0) return;
      // visibility:hidden 的子元素仍可能自行设为 visible。
      if (st.visibility !== 'visible') {
        if (number(st.opacity) < 1) throw new Error('隐藏透明容器的合成关系暂不支持');
        for(const child of el.children) visit(child,inheritedOpacity);
        return;
      }
      const b=rect(el), opacity=inheritedOpacity*number(st.opacity);
      if (!b.w || !b.h) {
        for (const child of el.children) visit(child,opacity);
        return;
      }
      if (b.x>=W || b.y>=H || b.x+b.w<=0 || b.y+b.h<=0) return;
      const why=complex(st,el,el===slide);
      if (why) {
        if (el === slide) throw new Error('整页效果不能冒充可编辑：'+why);
        if (b.w*b.h > W*H*.9) throw new Error('复杂元素覆盖整页，拒绝截图式导出：'+why);
        add(el,{kind:'rasterized',mode:'subtree',reason:why,box:b,textChars:rasterTextChars(el)});
        return;
      }
      const before=getComputedStyle(el,'::before'), after=getComputedStyle(el,'::after');
      const pseudo=generated(before)||generated(after);
      const borders=['Top','Right','Bottom','Left'].map(edge=>({width:number(st['border'+edge+'Width']),color:st['border'+edge+'Color'],style:st['border'+edge+'Style']}));
      const radius=number(st.borderTopLeftRadius);
      const uniform=borders.every(v=>v.width===borders[0].width && v.color===borders[0].color && v.style===borders[0].style);
      const radii=['TopLeft','TopRight','BottomLeft','BottomRight'].map(v=>st['border'+v+'Radius']);
      const complexBg=st.backgroundImage!=='none'||st.boxShadow!=='none'||pseudo||!uniform||new Set(radii).size>1||
        borders.some(v=>v.width && !['solid','none'].includes(v.style));
      if (complexBg) {
        const pseudoChars=[before,after].reduce((n,p)=>n+(!['none','normal','""',"''"].includes(p.content)?Math.max(0,p.content.length-2):0),0);
        add(el,{kind:'rasterized',mode:'background',reason:pseudo?'CSS pseudo/background':'CSS background/border/shadow',box:b,textChars:pseudoChars,
          pseudoColors:[before.color,after.color]});
      } else if (st.backgroundColor!=='rgba(0, 0, 0, 0)' || borders.some(v=>v.width)) {
        const localW=number(st.width), localH=number(st.height);
        add(el,{kind:'shape',box:b,fill:st.backgroundColor,opacity,
          border:borders[0],radius:st.borderTopLeftRadius.includes('%') ? Math.min(b.w,b.h)*radius/100 : radius*(b.w/localW||1),
          ellipse:radii.every(v=>v==='50%') || (radius>=Math.min(localW,localH)/2 && Math.abs(b.w-b.h)<1)});
      }
      if (el.tagName==='IMG') {
        add(el,{kind:'image',mode:'subtree',reason:'embedded image; browser object-fit',box:b,textChars:0});
        return;
      }
      const children=[...el.childNodes];
      // 原生对象按普通 DOM 绘制；兄弟 z-index 排序，不宣称支持任意 CSS stacking context。
      const ordered=children.map((child,index)=>({child,index,z:child.nodeType===1?number(getComputedStyle(child).zIndex):0}));
      ordered.sort((a,b)=>a.z-b.z||a.index-b.index);
      for (const {child} of ordered) {
        if (child.nodeType===1) visit(child,opacity);
        else if (child.nodeType===3 && child.data.trim()) {
          chars+=child.length;
          if(chars>50000) throw new Error('超过 50000 字符上限');
          const lines=textLines(child,root,{x:1/norm.x,y:1/norm.y},st,opacity);
          // 字体使用该元素真实 CSS 缩放；祖先 scale 不能只缩坐标不缩字号。
          const elementScaleY=el.offsetHeight?el.getBoundingClientRect().height/el.offsetHeight:scale.y;
          const elementScaleX=el.offsetWidth?el.getBoundingClientRect().width/el.offsetWidth:scale.x;
          for(const line of lines) {
            line.font=font(st,elementScaleX*norm.x,elementScaleY*norm.y,opacity,decorations(el));
            if (st.textTransform==='uppercase') line.text=line.text.toUpperCase();
            if (st.textTransform==='lowercase') line.text=line.text.toLowerCase();
            add(el,line);
          }
        }
      }
      if (el.tagName==='LI' && st.listStyleType!=='none') warnings.push({key:key(el),reason:'列表 marker 未转换；请使用 HTML 显式标记或局部图形'});
      if (number(st.zIndex)<0) warnings.push({key:key(el),reason:'负 z-index 的跨层叠关系可能近似'});
      if (b.x<-.5||b.y<-.5||b.x+b.w>W+.5||b.y+b.h>H+.5) warnings.push({key:key(el),reason:'元素超出 slide，截图裁剪；原生对象越界需复核'});
    }
    visit(slide);
    const fonts=[...document.fonts].filter(f=>f.status==='error').map(f=>f.family);
    if (fonts.length) throw new Error('字体加载失败：'+fonts.join(','));
    return {id:slide.dataset.slideId,width:W,height:H,elements,warnings,
      normalizedScale:scale,domTextChars:slide.innerText.trim().length};
  };

  window.pptxCaptureStyle = (key, mode, colors) => {
    const style=document.createElement('style'); style.id='pptx-capture-style';
    const target=`[data-pptx-key="${key}"]`;
    if(mode==='subtree') document.querySelector(target).querySelectorAll('*').forEach(el=>{
      if(getComputedStyle(el).visibility==='visible') el.setAttribute('data-pptx-capture-visible','');
    });
    style.textContent=`body,body * {visibility:hidden!important} ${target},${target}::before,${target}::after {visibility:visible!important}`;
    if(mode==='subtree') style.textContent+=`${target} [data-pptx-capture-visible] {visibility:visible!important}`;
    else style.textContent+=`${target} {-webkit-text-fill-color:transparent!important;text-shadow:none!important}
      ${target}::before {-webkit-text-fill-color:${colors[0]}!important}
      ${target}::after {-webkit-text-fill-color:${colors[1]}!important}`;
    document.head.append(style);
  };
  window.pptxClearCapture = () => {
    document.getElementById('pptx-capture-style')?.remove();
    document.querySelectorAll('[data-pptx-capture-visible]').forEach(el=>el.removeAttribute('data-pptx-capture-visible'));
  };
})();
