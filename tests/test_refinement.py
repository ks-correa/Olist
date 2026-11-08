"""Regresión del sobre temporal único y comunicación académica."""
import json
import shutil
import subprocess
from html.parser import HTMLParser
from typing import Any
from pathlib import Path
import numpy as np
import pytest
from streamlit.testing.v1 import AppTest
from src.dashboard_data import load_dashboard
from src.dashboard_metrics import PlayerState,snapshot
from ui.tanks import visual_payload,frame_payload,HTML,JS

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture(scope='module')
def data():
    return load_dashboard(ROOT)

def make_frame(data,index=1217,revision=1,playing=True,code='E0',window='principal',speed=168):
    series=data.get(window,code);snap=snapshot(series,index)
    quantities=np.column_stack([series.states[:,:3],series.states[:,3]-series.states[0,3]])
    maxima=np.maximum(1.,quantities.max(axis=0))
    p=visual_payload(snap,maxima,np.full(4,1000.),quantities.min(axis=0),quantities.max(axis=0),playing,window,code)
    return frame_payload(p,series,snap,revision,speed)

@pytest.mark.parametrize('speed',[1,6,24,72,168])
def test_speeds_pause_resume_and_single_frame(data,speed):
    player=PlayerState(index=1217,speed=speed);player.play(100.,5488)
    for revision,now in enumerate([100.5,101.,101.5],1):
        player.tick(now,5488)
        f=make_frame(data,player.index,revision,speed=speed)
        assert f['index']==f['chart']['index']==player.index
        assert f['date']==f['chart']['date']==snapshot(data.get('principal','E0'),player.index)['date']
        assert f['progress']==player.index/5488
        assert f['metrics'][0]['raw']==pytest.approx(sum(t['level'] for t in f['tanks'][:3]),rel=0,abs=1e-10)
    player.pause();paused=player.index;player.tick(500.,5488)
    assert player.index==paused
    player.play(600.,5488);player.tick(601.,5488)
    assert player.index==paused+speed

def test_reported_84_hour_case(data):
    old=make_frame(data,1217,1);new=make_frame(data,1301,2)
    assert old['date']=='2018-04-22 15:00' and new['date']=='2018-04-26 03:00'
    assert new['index']-old['index']==168*.5
    assert new['chart']['index']==new['index'] and new['chart']['date']==new['date']

def test_reject_inconsistent_snapshot(data):
    s=data.get('principal','E0');snap=snapshot(s,1)
    bad=make_frame(data,0)
    with pytest.raises(ValueError,match='fotograma'):
        frame_payload({k:bad[k] for k in ['index','date']},s,snap,2,168)

@pytest.mark.parametrize('index',[0,744])
def test_january_endpoints_and_transfers(data,index):
    f=make_frame(data,index,playing=False,window='sensibilidad_enero')
    assert f['chart']['index']==index and f['progress']==index/744
    assert all(not v['active'] for v in f['flows'])
    if index==0:
        assert all(t['incoming']=='Sin intervalo' for t in f['tanks'])
    else:
        assert f['status']=='Final de trayectoria'
        assert f['flows'][3]['value']==data.get('sensibilidad_enero','E0').flows[-1,2]
        assert f['tanks'][3]['outgoing']=='0,00'

def get_frame(at):
    return json.loads(at.get('bidi_component')[0].proto.json)

def test_one_publisher_and_context_changes():
    at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
    assert not at.sidebar.info
    at.switch_page('app_pages/simulation.py').run()
    assert len(at.get('bidi_component'))==1 and not at.metric and not at.get('plotly_chart')
    assert not at.warning
    at.slider(key='time_index').set_value(1301).run()
    f=get_frame(at);assert f['index']==1301 and f['date']==f['chart']['date']
    at.button(key='play').click().run()
    at.segmented_control(key='scenario').set_value('E2').run()
    f=get_frame(at)
    assert f['code']=='E2' and f['index']==f['chart']['index'] and not f['playing']
    at.selectbox(key='window').select('sensibilidad_enero').run()
    reset=get_frame(at)
    assert reset['index']==0 and reset['progress']==0 and reset['revision']>f['revision']
    assert not at.exception

def test_validation_unchanged_and_no_alarm(data):
    at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
    at.switch_page('app_pages/validation_view.py').run()
    assert not at.warning and not at.error and not at.exception
    assert [m.value for m in at.metric[:3]]==['0,995','0,559','0,666']
    assert at.metric[3].value=='≤ 0,30'
    assert data.validation_summary['decision']=='C'
    assert 'clasificación' in ' '.join(e.value for e in at.caption)
    assert all(data.validation.NRMSE.iloc[:3]>.30)

def test_frontend_rejects_late_frame_and_updates_every_readout(data,tmp_path):
    node=shutil.which('node')
    if node is None:
        pytest.skip('Node necesario para ejecutar la regresión JavaScript sin navegador')
    class TreeParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.root:dict[str,Any]=dict(tag='root',attrs={},children=[])
            self.stack:list[dict[str,Any]]=[self.root]
        def handle_starttag(self,tag,attrs):
            n=dict(tag=tag,attrs=dict(attrs),children=[])
            self.stack[-1]['children'].append(n);self.stack.append(n)
        def handle_endtag(self,tag):
            self.stack.pop()
    parser=TreeParser();parser.feed(HTML)
    module=tmp_path/'tanks.mjs';module.write_text(JS,encoding='utf-8')
    frames=[make_frame(data,1217,1),make_frame(data,1301,2),
            make_frame(data,0,3,False,window='sensibilidad_enero'),make_frame(data,5488,4,False)]
    fixture=tmp_path/'frames.json'
    fixture.write_text(json.dumps(dict(dom=parser.root,frames=frames)),encoding='utf-8')
    result=subprocess.run([node,str(ROOT/'tests/frontend_dom.mjs'),str(module),str(fixture)],capture_output=True,text=True,timeout=15)
    assert result.returncode==0,result.stdout+result.stderr
