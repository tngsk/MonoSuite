const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {Navigation,worldRect,fitCamera,zoomCamera,pinchCamera}=require('../src/mono_space/web/core.js');
test('all sections are reachable; overview and free modes preserve return target',()=>{
 const nav=new Navigation(['b','b'],['a','b','c']);assert.deepEqual(nav.route,['b']);
 for(const id of nav.route){nav.focus(id);assert.equal(nav.selectedId,id)}
 assert.equal(nav.adjacent(1),null);nav.explore();assert.equal(nav.mode,'free');
 nav.overview();assert.equal(nav.adjacent(1),'b');assert.equal(nav.selectedId,'b');
 nav.focus(nav.route[0]);assert.equal(nav.index,0);assert.throws(()=>nav.focus('missing'));
});
test('screen geometry converts rendered bounds including border and rotation extent',()=>{
 assert.deepEqual(worldRect({left:304,top:108,width:800,height:400},{left:100,top:-92},2),{x:102,y:100,w:400,h:200});
});
test('focus fits width regardless of height; overview still fits both axes',()=>{
 for(const view of [{w:1600,h:880},{w:390,h:844}]){
  const short={x:20,y:30,w:512,h:200},tall={...short,h:4000};
  const c=fitCamera(tall,view,true);
  assert.deepEqual(c,fitCamera(short,view,true));
  assert(c.s<=1.84);
  assert(c.x+(tall.x+tall.w)*c.s<=view.w*.92+1e-8);
  assert.equal(c.y+tall.y*c.s,view.h*.15);
  assert(c.y+(tall.y+tall.h)*c.s>view.h);
  const overview=fitCamera(tall,view,false);
  assert(overview.s*tall.h<=view.h);
  assert(overview.s*tall.w<=view.w);
 }
});
test('zoom keeps the point under the cursor fixed',()=>{
 const a={x:-200,y:100,s:1},b=zoomCamera(a,2,300,200);
 assert.equal((300-a.x)/a.s,(300-b.x)/b.s);assert.equal((200-a.y)/a.s,(200-b.y)/b.s);
});
test('pinch includes scale and midpoint translation',()=>{
 const c=pinchCamera({x:0,y:0,s:1},{x:100,y:100,distance:100},{x:130,y:120,distance:200});
 assert.deepEqual(c,{s:2,x:-70,y:-80});
});
test('app delegates animation and tokens have no direct cycles',()=>{
 const app=fs.readFileSync(require.resolve('../src/mono_space/web/app.js'),'utf8');assert(!app.includes('requestAnimationFrame'));assert(!app.includes('curves'));
 const css=fs.readFileSync(require.resolve('../src/mono_space/web/styles.css'),'utf8');assert(!/(--[\w-]+):\s*var\(\1\)/.test(css));
});
test('gesture handler continues smoothly from pinch to one finger and ignores duplicate release',()=>{
 global.SpatialCore=require('../src/mono_space/web/core.js');const input=require('../src/mono_space/web/input.js');
 const handlers=new Map();const viewport={clientHeight:800,getBoundingClientRect:()=>({left:10,top:20}),classList:{add(){},remove(){}},setPointerCapture(){},addEventListener:(key,fn)=>handlers.set(key,fn)};
 let camera={x:0,y:0,s:1};const gesture=input.attach(viewport,()=>camera,c=>camera=c,()=>{});
 const send=(type,id,x,y)=>handlers.get(type)({pointerId:id,clientX:x,clientY:y,button:0});
 send('pointerdown',1,110,120);send('pointerdown',2,210,120);send('pointermove',2,310,120);
 assert.equal(camera.s,2);assert(gesture.moved);
 send('pointerup',2,310,120);send('lostpointercapture',2,310,120);
 const x=camera.x;send('pointermove',1,130,120);assert.equal(camera.x,x+20);
 send('pointercancel',1,130,120);send('pointerdown',3,100,100);assert.equal(gesture.moved,false);
});

test('grid settings retain readable width and snap outer geometry',()=>{
 const {metrics,snap}=require('../src/mono_space/web/layout.js');
 for(const grid of [16,32,64]){
  const m=metrics({grid,bodyWidth:448,density:'standard'});
  assert.equal(m.body,448);
  for(const value of Object.values(m))assert.equal(value%grid,0);
  for(const size of [199.7,448,761]){const result=snap(size,grid);assert(result>=size);assert(result-size<grid);assert.equal(result%grid,0)}
 }
 assert.throws(()=>metrics({grid:24,bodyWidth:448,density:'standard'}));
});
test('layout planner is deterministic, non-mutating and grid aligned at every level',()=>{
 const {plan,metrics}=require('../src/mono_space/web/layout.js');
 for(const grid of [16,32,64]){
  const m=metrics({grid,bodyWidth:448,density:'standard'});
  const leaf=h=>({w:448,h,layout:'row',children:[]});
  const node={w:384,h:203,atlas:true,children:[{w:448,h:80,chapter:true,layout:'stack',children:[leaf(113),leaf(197)]},{w:448,h:90,chapter:true,layout:'compare',children:[leaf(70),leaf(203),leaf(101)]}]};
  const original=JSON.stringify(node),first=plan(node,m);
  for(let i=0;i<5;i++)assert.deepEqual(plan(node,m),first);
  assert.equal(JSON.stringify(node),original);
  function check(box){for(const key of ['x','y','w','h'])if(key in box)assert.equal(box[key]%grid,0);if(box.container)check({...box.container,children:[]});box.children.forEach(check)}
  check(first);assert.equal(first.children[0].h,first.children[1].h);
 }
});
test('motion limits pan distance and uses fade for scale changes',()=>{
 const {kind}=require('../src/mono_space/web/motion.js'),from={x:0,y:0,s:1},view={w:1000,h:800};
 assert.equal(kind(from,{x:100,y:80,s:1},view),'pan');
 assert.equal(kind(from,{x:751,y:0,s:1},view),'fade');
 assert.equal(kind(from,{x:0,y:0,s:1.84},view),'fade');
});

test('adjacent section travel pans despite a small fitting scale difference',()=>{
 const {kind}=require('../src/mono_space/web/motion.js');
 assert.equal(kind({x:0,y:0,s:1.84},{x:0,y:-600,s:1.84},{w:1440,h:900}),'pan');
 assert.equal(kind({x:0,y:0,s:1.84},{x:0,y:-400,s:1.82},{w:1440,h:900}),'pan');
 assert.equal(kind({x:0,y:0,s:1.84},{x:0,y:-1500,s:1.84},{w:1440,h:900}),'fade');
});

test('two-way comparison is top-aligned; three-way retains centre positioning',()=>{
 const {plan,metrics}=require('../src/mono_space/web/layout.js');
 const leaf=h=>({w:448,h,layout:'row',children:[]});
 const pair=plan({w:448,h:64,layout:'compare',children:[leaf(100),leaf(240)]},metrics());
 assert.equal(pair.children[0].y,0);assert.equal(pair.children[1].y,0);
 assert.equal(pair.children[0].w,pair.children[1].w);
 const triple=plan({w:448,h:64,layout:'compare',children:[leaf(300),leaf(100),leaf(200)]},metrics());
 assert(triple.children[1].y>0);assert(triple.children[2].y>0);
});

test('standard navigation skips empty chapters but keeps them selectable',()=>{
 const nav=new Navigation(['title','topic','next'],['title','chapter','topic','next']);
 assert.deepEqual(nav.route,['title','topic','next']);
 nav.focus('chapter');
 assert.equal(nav.adjacent(1),'topic');
 assert.equal(nav.adjacent(-1),'title');
});
