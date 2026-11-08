"""Datos visuales y sincronización del SVG, sin afirmar inspección del navegador."""
from pathlib import Path
import hashlib
import json
import time
import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest
from src.dashboard_data import load_dashboard, export_csv
from src.dashboard_metrics import snapshot
from ui.components import number, presentation_table
from ui.tanks import visual_payload

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture(scope='module')
def data():
    return load_dashboard(ROOT)

def payload(data,window,code,index,playing=True):
    s=data.get(window,code)
    maxima=np.r_[data.visual_maxima(window),max(1.,*(data.get(window,c).states[-1,3]-data.get(window,c).states[0,3] for c in ['E0','E1','E2']))]
    quantities=np.column_stack([s.states[:,:3],s.states[:,3]-s.states[0,3]])
    return visual_payload(snapshot(s,index),maxima,np.full(4,1000.),quantities.min(axis=0),
                          quantities.max(axis=0),playing,window,code)

@pytest.mark.parametrize('window',['principal','sensibilidad_enero'])
@pytest.mark.parametrize('code',['E0','E1','E2'])
@pytest.mark.parametrize('position',['initial','middle','final'])
def test_heights_flows_dates_and_terminal(data,window,code,position):
    s=data.get(window,code)
    index={'initial':0,'middle':s.duration//2,'final':s.duration}[position]
    p=payload(data,window,code,index)
    assert p['index']==index and p['date']==snapshot(s,index)['date']
    for i,t in enumerate(p['tanks']):
        expected=s.states[index,i] if i<3 else s.states[index,3]-s.states[0,3]
        assert t['quantity']==expected
        assert t['ratio']==expected/t['scale'] and 0<=t['ratio']<=1
        assert t['level']==s.states[index,i]
    assert p['tanks'][3]['total']==number(s.states[index,3])
    for i,f in enumerate(p['flows']):
        assert (f['source'],f['target'])==('Compras' if i==0 else f'T{i}',f'T{i+1}')
        expected=None if index==0 else np.r_[s.purchases[index-1],s.flows[index-1]][i]
        assert f['value']==expected
        assert f['active']==(expected is not None and expected>0)

@pytest.mark.parametrize('window',['principal','sensibilidad_enero'])
def test_common_scales(data,window):
    scales=[[t['scale'] for t in payload(data,window,c,168)['tanks']] for c in ['E0','E1','E2']]
    np.testing.assert_array_equal(scales[0],scales[1])
    np.testing.assert_array_equal(scales[0],scales[2])

def test_zero_paused_and_magnitude(data):
    s=snapshot(data.get('principal','E0'),10)
    s['incoming']=np.array([0.,1.,100.,1000.])
    args=(s,np.full(4,1e6),np.full(4,1000.),np.zeros(4),np.full(4,1e6))
    p=visual_payload(*args,True,'principal','E0')
    assert not p['flows'][0]['active'] and not p['flows'][0]['visible']
    assert p['flows'][1]['period']>p['flows'][2]['period']>p['flows'][3]['period']
    assert all(not f['active'] for f in visual_payload(*args,False,'principal','E0')['flows'])

@pytest.mark.parametrize('value,expected',[(1e-200,'≈ 0'),(-1e-7,'≈ 0'),(0.,'0,00'),(12345.678,'12.345,68'),(13_339_474.306616245,'13.339.474,31'),(.995,'0,99')])
def test_readable_numbers(value,expected):
    assert number(value)==expected

def test_table_format_does_not_change_data_or_csv():
    f=pd.DataFrame({'X4_incremental':[1e-150,12345.6789],'sesgo_medio':[-.000001,2.5]})
    before=f.copy(deep=True);csv=export_csv(f)
    rendered=presentation_table(f)
    assert rendered.iloc[0,0]=='≈ 0' and rendered.iloc[1,0]=='12.345,68'
    assert list(rendered)==['Entregas de la ventana','Sesgo medio (pedidos)']
    pd.testing.assert_frame_equal(f,before)
    assert export_csv(f)==csv

def component_payload(at):
    components=at.get('bidi_component')
    assert len(components)==1
    assert components[0].proto.component_name=='olist.connected_tanks'
    return json.loads(components[0].proto.json)

def test_component_and_controls_share_one_index():
    at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
    at.switch_page('app_pages/simulation.py').run()
    initial=component_payload(at)
    assert initial['index']==0 and initial['tanks'][3]['ratio']==0
    assert all(f['value'] is None for f in initial['flows'])
    at.slider(key='time_index').set_value(321).run()
    at.session_state.player.playing=True
    at.session_state.player.last_tick=time.monotonic()+100
    at.segmented_control(key='scenario').set_value('E1').run()
    switched=component_payload(at)
    assert switched['index']==321 and switched['code']=='E1' and not switched['playing']
    assert [t['scale'] for t in initial['tanks']]==[t['scale'] for t in switched['tanks']]
    at.selectbox(key='window').select('sensibilidad_enero').run()
    january=component_payload(at)
    assert january['index']==0 and january['window']=='sensibilidad_enero' and not january['playing']
    at.slider(key='time_index').set_value(744).run()
    final=component_payload(at)
    assert final['index']==744 and not final['playing'] and at.button(key='play').disabled
    assert not at.exception

def test_scientific_files_unchanged():
    manifest=json.loads((ROOT/'reports/integridad_redisenio.json').read_text(encoding='utf-8'))
    for name,expected in manifest.items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected,name
