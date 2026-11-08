// DOM mínimo para ejercitar el renderer real en Node. No renderiza CSS ni sustituye al navegador.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {pathToFileURL} from 'node:url';
const [modulePath,fixturePath]=process.argv.slice(2);
const {default:render}=await import(pathToFileURL(modulePath));
const fixture=JSON.parse(fs.readFileSync(fixturePath,'utf8'));
class Element {
 constructor(tag,attrs={}) {this.tag=tag;this.attrs={...attrs};this.children=[];this.dataset={};this.style={};this._text='';
  this.classList={toggle:(name,on)=>{const classes=new Set((this.attrs.class??'').split(' '));on?classes.add(name):classes.delete(name);this.attrs.class=[...classes].join(' ');}};
 }
 appendChild(el) {this.children.push(el);return el;}
 setAttribute(k,v) {this.attrs[k]=String(v);}
 getAttribute(k) {return this.attrs[k];}
 set className(v) {this.attrs.class=v;}
 get className() {return this.attrs.class;}
 set textContent(v) {this._text=String(v);this.children=[];}
 get textContent() {return this._text+this.children.map(c=>c.textContent).join('');}
 matches(selector) {
  if(selector.startsWith('#')) return this.attrs.id===selector.slice(1);
  if(selector.startsWith('.')) return (this.attrs.class??'').split(' ').includes(selector.slice(1));
  if(selector.startsWith('[')) {const match=selector.match(/^\[([^=\]]+)(?:="([^"]*)")?\]$/);return match && match[1] in this.attrs && (match[2]===undefined || this.attrs[match[1]]===match[2]);}
  return this.tag===selector;
 }
 querySelector(selector) {
  for(const c of this.children) {if(c.matches(selector)) return c;const nested=c.querySelector(selector);if(nested)return nested;}
  return null;
 }
}
function build(n) {const el=new Element(n.tag,n.attrs);for(const child of n.children)el.appendChild(build(child));return el;}
globalThis.document={createElementNS:(_,tag)=>new Element(tag),createElement:tag=>new Element(tag)};
const parent=build(fixture.dom),root=parent.querySelector('.plant');
function check(f) {
 assert.equal(root.dataset.index,String(f.index));
 assert.ok(root.querySelector('#plant-time').textContent.includes(f.date));
 assert.ok(root.querySelector('#frame-status').textContent.includes(f.date));
 assert.equal(root.querySelector('#frame-progress').value,f.progress);
 assert.equal(root.querySelector('#chart-marker').getAttribute('x1'),String(f.chart.marker));
 assert.ok(root.querySelector('#chart-marker').getAttribute('aria-label').includes(f.date));
 f.tanks.forEach((t,i)=>{const tank=root.querySelector(`[data-tank="${i}"]`);assert.equal(tank.querySelector('[data-value]').textContent,t.value);assert.equal(tank.querySelector('.fill').style.transform,`scaleY(${t.ratio})`);});
 f.flows.forEach((flow,i)=>{const path=root.querySelector(`[data-pipe="${i}"]`).querySelector('.flow');assert.equal(path.style.animationPlayState,flow.active?'running':'paused');assert.equal(path.style.opacity,flow.visible?'1':'0');});
 f.metrics.forEach((metric,i)=>assert.equal(root.querySelector('#frame-metrics').children[i].querySelector('.metric-value').textContent,metric.value));
}
render({data:fixture.frames[0],parentElement:parent});check(fixture.frames[0]);
render({data:fixture.frames[1],parentElement:parent});check(fixture.frames[1]);
// Simula un import CCv2 antiguo que termina después del más reciente.
render({data:fixture.frames[0],parentElement:parent});check(fixture.frames[1]);
for(const frame of fixture.frames.slice(2)) {render({data:frame,parentElement:parent});check(frame);}
console.log('Renderer real: revisiones fuera de orden rechazadas; todos los indicadores pertenecen al mismo fotograma. DOM simulado, sin inspeccion visual.');
