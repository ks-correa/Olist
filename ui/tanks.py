"""SVG persistente CCv2: interpreta estados, nunca integra ni modifica datos."""
import numpy as np
import streamlit as st
from ui.components import number

TANK_NAMES = ['Pendientes de aprobación', 'Pendientes de despacho',
              'Pendientes de entrega', 'Entregados acumulados']
FLOW_NAMES = ['Pedidos recibidos durante la última hora',
              'Pedidos aprobados durante la última hora',
              'Pedidos despachados durante la última hora',
              'Pedidos entregados durante la última hora']


def visual_payload(snap, maxima, flow_maxima, minima, observed_maxima, playing, window, code):
    """Alturas relativas exactas y movimiento condicionado al intervalo activo."""
    maxima = np.asarray(maxima, dtype=float)
    if maxima.shape != (4,) or not np.isfinite(maxima).all() or (maxima <= 0).any():
        raise ValueError('Se requieren cuatro escalas visuales positivas')
    quantities = np.r_[snap['levels'][:3], snap['deliveries']]
    if (quantities < 0).any() or (quantities > maxima * (1 + 1e-12)).any():
        raise ValueError('Nivel fuera de la escala visual')
    tanks = []
    for i in range(4):
        delta = None if snap['delta'] is None else float(snap['delta'][i])
        tanks.append(dict(name=TANK_NAMES[i], level=float(snap['levels'][i]),
            quantity=float(quantities[i]), ratio=float(quantities[i]/maxima[i]),
            scale=float(maxima[i]), value=number(quantities[i]), total=number(snap['levels'][i]),
            scale_text=number(maxima[i], 0),
            delta='Sin hora anterior' if delta is None else number(delta),
            incoming='Sin intervalo' if snap['incoming'] is None else number(snap['incoming'][i]),
            outgoing='Sin intervalo' if snap['flows'] is None else number(snap['flows'][i] if i<3 else 0.),
            range_text=f'Mín. {number(minima[i])} · Máx. {number(observed_maxima[i])}'))
    flows = []
    for i in range(4):
        value = None if snap['incoming'] is None else float(snap['incoming'][i])
        relative = 0. if value is None else min(1., value/max(1., float(flow_maxima[i])))
        flows.append(dict(source='Compras' if i == 0 else f'T{i}', target=f'T{i+1}',
            label=['λ(t)', 'q12', 'q23', 'q34'][i], name=FLOW_NAMES[i], value=value,
            text='Sin intervalo' if value is None else number(value),
            active=bool(playing and value is not None and value > 0),
            visible=bool(value is not None and value > 0),
            period=float(2.6 - 1.8*np.sqrt(relative))))
    return dict(index=snap['index'], date=snap['date'], window=window, code=code,
                playing=bool(playing), tanks=tanks, flows=flows)


def frame_payload(payload, series, snap, revision, speed):
    """Un sobre inmutable lógico: todas las salidas actuales se pintan juntas."""
    index=snap['index']
    if payload['index']!=index or payload['date']!=snap['date']:
        raise ValueError('El fotograma no corresponde a la fotografía seleccionada')
    lo=max(0,index-120);hi=min(series.duration+1,max(169,index+49))
    values=series.states[lo:hi,:3]
    top=max(1.,float(values.max()))
    x=60+np.arange(hi-lo)*1100/max(1,hi-lo-1)
    paths=[' '.join(f'{px:.4f},{py:.4f}' for px,py in zip(x,220-values[:,i]/top*180)) for i in range(3)]
    status='Reproduciendo' if payload['playing'] else 'Final de trayectoria' if index==series.duration else 'En pausa'
    return dict(**payload, revision=int(revision),duration=series.duration,speed=int(speed),status=status,
        progress=index/series.duration,
        metrics=[dict(label=label,value=number(snap[key]),raw=float(snap[key]),unit='pedidos')
            for label,key in [('Pendientes P','pending'),('Entregas incrementales','deliveries'),
                              ('Compras acumuladas','purchases'),('Error de conservación','conservation')]],
        chart=dict(index=index,date=snap['date'],paths=paths,marker=float(60+(index-lo)*1100/max(1,hi-lo-1)),
                   top=number(top,0),first=str(series.dates[lo])[:16].replace('T',' '),
                   last=str(series.dates[hi-1])[:16].replace('T',' ')))


HTML = """
<section class="plant" aria-label="Cuatro tanques virtuales de pedidos conectados">
 <header><span class="plant-label">SISTEMA LOGÍSTICO / CUATRO AGENTES</span><span id="plant-time"></span></header>
 <div class="scroll" tabindex="0" role="region" aria-label="Diagrama de tanques; desplazamiento horizontal disponible">
  <svg viewBox="0 0 1220 420" role="img" aria-labelledby="plant-title plant-description">
   <title id="plant-title">Compras y cuatro tanques virtuales interconectados</title>
   <desc id="plant-description">Niveles y transferencias agregadas del instante seleccionado.</desc>
   <defs>
    <pattern id="blocks" width="18" height="14" patternUnits="userSpaceOnUse"><rect x="2" y="2" width="12" height="8" rx="1" fill="white" opacity=".2"/></pattern>
    <marker id="direction" markerWidth="7" markerHeight="7" refX="5" refY="3.5" orient="auto"><path d="M0 0 L6 3.5 L0 7" fill="none" stroke="#087f8c" stroke-width="1.4"/></marker>
   </defs>
   <g id="pipes"></g><g id="tanks"></g>
  </svg>
 </div>
 <footer><span>Escalas relativas: referencia de dibujo, no capacidad física real</span><span>Entrada y salida: pedidos de la última hora · Bloques y trazos agregados, no pedidos individuales</span></footer>
 <div id="frame-readouts" hidden>
  <p id="frame-status"></p>
  <progress id="frame-progress" max="1" aria-label="Avance de la ventana seleccionada"></progress>
  <div id="frame-metrics" class="metrics"></div>
  <details open><summary>Estado sincronizado · contexto horario cercano</summary>
   <div class="scroll"><svg class="context-chart" viewBox="0 0 1220 285" role="img" aria-label="Niveles de T1, T2 y T3; marcador del instante actual">
    <text x="60" y="22" class="small">Pedidos</text><text x="60" y="43" class="small" id="chart-top"></text>
    <path d="M60 40 V220 H1160" fill="none" stroke="#cedde4"/>
    <polyline id="chart-0" fill="none" stroke="#087f8c" stroke-width="2"/>
    <polyline id="chart-1" fill="none" stroke="#347ba0" stroke-width="2"/>
    <polyline id="chart-2" fill="none" stroke="#d18a3a" stroke-width="2"/>
    <line id="chart-marker" y1="40" y2="220" stroke="#087f8c" stroke-dasharray="4 4"/>
    <text x="60" y="241" class="small" id="chart-first"></text><text x="1160" y="241" text-anchor="end" class="small" id="chart-last"></text>
    <text x="480" y="270" fill="#087f8c">T1 · Aprobación</text><text x="670" y="270" fill="#347ba0">T2 · Despacho</text><text x="850" y="270" fill="#d18a3a">T3 · Entrega</text>
   </svg></div>
  </details>
 </div>
</section>
"""

CSS = """
.plant {color:var(--st-text-color,#173347);background:var(--st-background-color,#f7fafc);border:1px solid #cedde4;border-radius:16px;padding:12px 16px 10px;font-family:var(--st-font,'Arial'),sans-serif;}
header,footer {display:flex;justify-content:space-between;flex-wrap:wrap;gap:6px;align-items:center;}
header {font-size:12px;} .plant-label {letter-spacing:1.5px;font-weight:700;color:#087f8c;}
#plant-time {font-variant-numeric:tabular-nums;font-weight:600;}
footer {font-size:11px;color:#526a78;border-top:1px solid #dce6eb;padding-top:8px;}
.scroll {overflow-x:auto;overscroll-behavior-x:contain;} svg {display:block;width:100%;min-width:1000px;height:auto;}
svg text {fill:var(--st-text-color,#173347);font-size:13px;font-family:var(--st-font,'Arial'),sans-serif;}
.tag {font-weight:700;font-size:12px;letter-spacing:1px;fill:#087f8c;}
.station-name {font-size:16px;font-weight:600;} .quantity {font-size:25px;font-weight:700;font-variant-numeric:tabular-nums;}
.small {font-size:11px;fill:#526a78;} .range {font-size:11px;fill:#526a78;} .total {font-size:13px;font-weight:600;}
.shell {fill:#edf3f6;stroke:#648392;stroke-width:2;}
.fill {transform-box:fill-box;transform-origin:center bottom;transition:transform .35s ease-out;}
.first .fill {transition:none;} .pipe {fill:none;stroke:#c8d8df;stroke-width:12;stroke-linejoin:round;}
.paused .fill {transition:none;}
.metrics {display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;margin:12px 0;}
.metric {border:1px solid #cedde4;border-radius:10px;padding:12px;}
.metric-label,.metric-unit {display:block;font-size:12px;}.metric-value {display:block;font-size:26px;font-weight:600;}
#frame-status {font-size:13px;margin:10px 0;} #frame-progress {width:100%;height:6px;accent-color:#087f8c;}
summary {font-size:14px;cursor:pointer;padding:8px 0;}
.pipe-core {fill:none;stroke:#eaf1f5;stroke-width:7;stroke-linejoin:round;}
.flow {fill:none;stroke:#087f8c;stroke-width:4;stroke-dasharray:5 16;animation:transfer 1.5s linear infinite;animation-play-state:paused;}
.flow-label {font-weight:700;font-size:12px;} .flow-number {font-size:11px;font-variant-numeric:tabular-nums;}
@keyframes transfer {to {stroke-dashoffset:-42;}}
@media(prefers-reduced-motion:reduce) {.flow {animation:none !important;} .fill {transition:none !important;}}
"""

JS = """
export default function({data, parentElement}) {
 const root=parentElement.querySelector('.plant');
 // Un callback síncrono publica todo el fotograma. Nunca avanza el reloj localmente.
 // CCv2 puede terminar imports asíncronos fuera de orden: no aceptar revisiones antiguas.
 if(data.revision!==undefined && Number(root.dataset.revision??-1)>data.revision) return;
 const ns='http://www.w3.org/2000/svg';
 const make=(tag,attrs,parent,text)=>{
  const el=document.createElementNS(ns,tag);
  for(const [k,v] of Object.entries(attrs)) el.setAttribute(k,v);
  if(text!==undefined) el.textContent=text;
  parent.appendChild(el);return el;
 };
 const xs=[160,430,700,970];
 const colors=['#087f8c','#347ba0','#d18a3a','#26836d'];
 const subtitles=[['Pendientes de','aprobación'],['Pendientes de','despacho'],['Pendientes de','entrega'],['Entregados','acumulados']];
 // Sólo se construye el dibujo una vez. Los siguientes fotogramas actualizan nodos.
 if(!root.dataset.built) {
  const tanks=root.querySelector('#tanks'),pipes=root.querySelector('#pipes');
  xs.forEach((x,i)=>{
   const g=make('g',{'data-tank':i},tanks);
   make('text',{x:x+90,y:25,'text-anchor':'middle',class:'tag'},g,`T${i+1}`);
   subtitles[i].forEach((t,j)=>make('text',{x:x+90,y:48+j*20,'text-anchor':'middle',class:'station-name'},g,t));
   make('text',{x:x+90,y:105,'text-anchor':'middle',class:'quantity','data-value':''},g);
   make('text',{x:x+90,y:124,'text-anchor':'middle',class:'small'},g,i===3?'Entregas de esta ventana':'Nivel actual · pedidos');
   make('rect',{x,y:140,width:180,height:155,rx:12,class:'shell'},g);
   const fill=make('g',{class:'fill'},g);
   make('rect',{x:x+5,y:145,width:170,height:145,rx:7,fill:colors[i]},fill);
   make('rect',{x:x+5,y:145,width:170,height:145,rx:7,fill:'url(#blocks)'},fill);
   [0,1,2,3].forEach(j=>make('path',{d:`M${x+9} ${150+j*43} h9`,stroke:'#648392','stroke-width':1},g));
   make('text',{x:x+90,y:318,'text-anchor':'middle',class:i===3?'total':'range','data-detail':''},g);
   make('text',{x:x+90,y:337,'text-anchor':'middle',class:'small'},g,'Cambio respecto a la hora anterior');
   make('text',{x:x+90,y:354,'text-anchor':'middle',class:'small','data-delta':''},g);
   make('text',{x:x+90,y:375,'text-anchor':'middle',class:'small','data-inout':''},g);
   make('text',{x:x+90,y:398,'text-anchor':'middle',class:'small','data-scale':''},g);
  });
  xs.forEach((x,i)=>{
   const start=i===0?28:xs[i-1]+180;
   const g=make('g',{'data-pipe':i},pipes);
   const d=`M${start} 220 H${x}`;
   make('path',{d,class:'pipe'},g);make('path',{d,class:'pipe-core','marker-end':'url(#direction)'},g);
   make('path',{d,class:'flow'},g);
   make('text',{x:(start+x)/2,y:182,'text-anchor':'middle',class:'flow-label'},g,['λ(t)','q12','q23','q34'][i]);
   make('text',{x:(start+x)/2,y:200,'text-anchor':'middle',class:'flow-number','data-flow-value':''},g);
   make('title',{},g);
  });
  make('text',{x:80,y:148,'text-anchor':'middle',class:'tag'},pipes,'COMPRAS');
  root.dataset.built='true';
 }
 const first=root.dataset.window!==data.window;
 root.classList.toggle('first',first);
 root.classList.toggle('paused',!data.playing);
 root.dataset.window=data.window;root.dataset.index=String(data.index);
 root.querySelector('#plant-time').textContent=`${data.code} · ${data.date} · Hora ${data.index}`;
 data.tanks.forEach((t,i)=>{
  const g=root.querySelector(`[data-tank="${i}"]`);
  const fill=g.querySelector('.fill');
  fill.style.transform=`scaleY(${t.ratio})`;
  fill.setAttribute('data-ratio',String(t.ratio));
  g.querySelector('[data-value]').textContent=t.value;
  g.querySelector('[data-detail]').textContent=i===3?`Total acumulado: ${t.total}`:t.range_text;
  g.querySelector('[data-delta]').textContent=t.delta;
  g.querySelector('[data-inout]').textContent=`Entrada: ${t.incoming} · Salida: ${t.outgoing}`;
  g.querySelector('[data-scale]').textContent=`Escala relativa: ${t.scale_text} pedidos`;
  g.setAttribute('aria-label',`${t.name}: ${t.total} pedidos; ${i===3?'incremento '+t.value:t.range_text}`);
 });
 data.flows.forEach((f,i)=>{
  const g=root.querySelector(`[data-pipe="${i}"]`),path=g.querySelector('.flow');
  path.style.animationDuration=`${f.period}s`;
  path.style.animationPlayState=f.active?'running':'paused';
  path.style.opacity=f.visible?'1':'0';
  g.querySelector('[data-flow-value]').textContent=f.text;
  g.querySelector('title').textContent=`${f.name}: ${f.text} pedidos. ${f.source} → ${f.target}`;
 });
 if(data.revision!==undefined) {
  root.querySelector('#frame-readouts').hidden=false;
  root.querySelector('#frame-status').textContent=`${data.status} · ${data.date} · Hora ${data.index} de ${data.duration} · ${data.speed} horas simuladas por segundo real`;
  const progress=root.querySelector('#frame-progress');progress.value=data.progress;
  progress.setAttribute('aria-valuetext',`Hora ${data.index} de ${data.duration}`);
  const metrics=root.querySelector('#frame-metrics');
  if(!metrics.children.length) data.metrics.forEach(()=>{
   const card=document.createElement('div');card.className='metric';
   for(const name of ['label','value','unit']) {const el=document.createElement('span');el.className=`metric-${name}`;card.appendChild(el);}
   metrics.appendChild(card);
  });
  data.metrics.forEach((metric,i)=>{
   for(const name of ['label','value','unit']) metrics.children[i].querySelector(`.metric-${name}`).textContent=metric[name];
  });
  data.chart.paths.forEach((points,i)=>root.querySelector(`#chart-${i}`).setAttribute('points',points));
  const marker=root.querySelector('#chart-marker');
  marker.setAttribute('x1',data.chart.marker);marker.setAttribute('x2',data.chart.marker);
  marker.setAttribute('aria-label',`Hora ${data.chart.index} · ${data.chart.date}`);
  for(const name of ['top','first','last']) root.querySelector(`#chart-${name}`).textContent=data.chart[name];
  root.dataset.revision=String(data.revision);
 }
 root.querySelector('#plant-description').textContent=`${data.date}, hora ${data.index}. `+
  data.tanks.map((t,i)=>`T${i+1}: ${t.total} pedidos${i===3?', incremento '+t.value:''}`).join('. ');
}
"""

_TANKS = st.components.v2.component('olist.connected_tanks', html=HTML, css=CSS, js=JS)


def connected_tanks(payload):
    return _TANKS(data=payload, key='connected_tanks', width='stretch', height='content')
