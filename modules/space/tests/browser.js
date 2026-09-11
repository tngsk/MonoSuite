(async()=>{
 const frame=document.querySelector('iframe'),results=[];
 const assert=(condition,message)=>{if(!condition)throw Error(message)};
 const waitFor=async predicate=>{for(let i=0;i<200;i++){if(predicate())return;await new Promise(r=>setTimeout(r,25))}throw Error('Timed out waiting for presentation')};
 try{
 frame.srcdoc=source;await waitFor(()=>frame.contentDocument?.documentElement.dataset.ready==='true');
 const doc=frame.contentDocument,win=frame.contentWindow;
 const picker=doc.querySelector('#section-picker'),world=doc.querySelector('#world'),viewport=doc.querySelector('#viewport');
 const select=id=>{picker.click();doc.querySelector(`#section-toc [data-section="${id}"]`).click()};
 const toggle=doc.querySelector('#reduce-motion');toggle.checked=true;toggle.dispatchEvent(new win.Event('change'));
 const data=JSON.parse(doc.querySelector('#data').textContent);


 const origin=world.getBoundingClientRect(),scale=origin.width/world.offsetWidth;
 for(const node of doc.querySelectorAll('.node')){
  const r=node.getBoundingClientRect();
  for(const value of [(r.left-origin.left)/scale,(r.top-origin.top)/scale,r.width/scale,r.height/scale])assert(Math.abs(value/32-Math.round(value/32))<.01,'Node off grid');
 }
 results.push('PASS: section origins and outer sizes match 32px grid');
 const layoutSnapshot=()=>[...doc.querySelectorAll('.node')].map(el=>[el.style.left,el.style.top,el.style.width,el.style.height]);
 const initialLayout=JSON.stringify(layoutSnapshot());
 for(let pass=0;pass<3;pass++){
  win.dispatchEvent(new win.Event('resize'));
  await new Promise(r=>setTimeout(r,200));
  assert(JSON.stringify(layoutSnapshot())===initialLayout,'Repeated layout changed geometry');
 }
 results.push('PASS: repeated DOM reflow is stable');

 for(const node of data.nodes){
 select(node.id);assert(picker.textContent===node.title,'Section label mismatch');
 const before=world.style.transform;await new Promise(r=>setTimeout(r,30));assert(world.style.transform===before,'Unexpected animated camera');
 assert(!doc.querySelector('#focus-indicator'),'Unexpected focus marker');
 }
 results.push('PASS: every section reachable; labels and immediate camera updates');
 assert(doc.querySelector('#section-toc').hidden,'TOC did not close after selection');
 picker.click();const beforeEscape=world.style.transform;
 doc.activeElement.dispatchEvent(new win.KeyboardEvent('keydown',{key:'Escape',bubbles:true}));
 assert(doc.querySelector('#section-toc').hidden,'Escape did not close TOC');
 assert(world.style.transform===beforeEscape,'Escape moved camera while dismissing TOC');
 picker.click();viewport.dispatchEvent(new win.PointerEvent('pointerdown',{bubbles:true}));
 assert(doc.querySelector('#section-toc').hidden,'Outside click did not close TOC');
 viewport.dispatchEvent(new win.PointerEvent('pointercancel',{bubbles:true}));
 results.push('PASS: TOC selection, Escape, outside click');
 select('question');
 assert(win.getComputedStyle(doc.querySelector('[data-id="question"] > .content')).opacity==='1','Focused area faded');
 assert(win.getComputedStyle(doc.querySelector('[data-id="intro"] > .content')).opacity==='0.25','Other area not at 25%');
 select('compare');
 assert(win.getComputedStyle(doc.querySelector('[data-id="maker"] > .content')).opacity==='1','Subtree child faded');
 results.push('PASS: 25% context and nested focus visibility');
 win.dispatchEvent(new win.KeyboardEvent('keydown',{key:'0',bubbles:true}));assert(picker.dataset.selected==='','0 key failed');
 win.dispatchEvent(new win.KeyboardEvent('keydown',{key:'1',bubbles:true}));assert(picker.dataset.selected===data.route[0],'1 key failed');
 const transform=world.style.transform;
 viewport.dispatchEvent(new win.WheelEvent('wheel',{deltaY:60,bubbles:true,cancelable:true}));
 assert(picker.dataset.selected==='','Free exploration left stale picker');assert(!doc.querySelector('.context-muted'),'Exploration did not restore opacity');assert(world.style.transform!==transform,'Wheel pan failed');
 win.dispatchEvent(new win.KeyboardEvent('keydown',{key:'o'}));assert(doc.querySelector('#status').textContent==='全体','Overview failed');
 results.push('PASS: 0 key, free mode, overview');
 assert([...doc.images].every(i=>i.complete&&i.naturalWidth>0),'Image decoding failed');
 select('image-close');const img=doc.querySelector('[data-id="image-close"] img').getBoundingClientRect();
 assert(img.left>=0&&img.right<=viewport.clientWidth,'Image focus clipped');
 const pointer=(type,id,x,y)=>viewport.dispatchEvent(new win.PointerEvent(type,{pointerId:id,clientX:x,clientY:y,pointerType:'touch',button:0,bubbles:true}));
 // Synthetic pointer events are not active OS pointers; suppress capture for this fixture.
 viewport.setPointerCapture=()=>{};
 const pre=world.style.transform;pointer('pointerdown',1,200,200);pointer('pointerdown',2,300,200);pointer('pointermove',2,400,200);pointer('pointerup',2,400,200);pointer('pointerup',1,200,200);
 assert(world.style.transform!==pre,'Pinch failed');results.push('PASS: embedded images, image framing, pinch handler');
 // A separate load checks browser decoding failures, rather than only file extension checks.
 const broken=JSON.parse(JSON.stringify(data));const key=Object.keys(broken.assets)[0];broken.assets[key]='data:image/png;base64,AAAA';
 frame.srcdoc=source.replace(/(<script id="data" type="application\/json">)[\s\S]*?(<\/script>)/,(_,a,b)=>a+JSON.stringify(broken).replace(/</g,'\\u003c')+b);
 await new Promise(r=>setTimeout(r,50));await waitFor(()=>frame.contentDocument?.documentElement.dataset.ready==='true');
 assert(frame.contentDocument.querySelector('.image-error'),'No image failure notice');results.push('PASS: corrupt image fallback');
 document.querySelector('#result').textContent=results.join('\n');document.documentElement.dataset.result='pass';
 }catch(error){document.querySelector('#result').textContent=results.join('\n')+'\nFAIL: '+error.stack;document.documentElement.dataset.result='fail'}
})();
