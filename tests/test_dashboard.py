"""Regresión de lectura, reloj, exportación e interfaz de la fase 6."""
from pathlib import Path
from io import BytesIO
import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest
from src.dashboard_data import load_dashboard, export_csv, custom_experiment, file_signature
from src.dashboard_metrics import PlayerState, snapshot

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture(scope='module')
def data():
    return load_dashboard(ROOT)

@pytest.mark.parametrize('window,duration', [('principal',5488),('sensibilidad_enero',744)])
@pytest.mark.parametrize('code',['E0','E1','E2'])
def test_series_export_and_snapshot(data,window,duration,code):
    s=data.get(window,code)
    assert s.duration==duration
    assert snapshot(s,0)['flows'] is None
    final=snapshot(s,duration)
    np.testing.assert_array_equal(final['flows'],s.flows[-1])
    assert abs(final['conservation'])<1e-6
    assert final['deliveries']==s.states[-1,3]-s.states[0,3]
    f=pd.read_csv(BytesIO(export_csv(s.frame())))
    assert len(f)==duration+1 and set(f.escenario)=={code} and set(f.ventana)=={window}
    assert pd.isna(f.q12_integrado.iloc[0])
    np.testing.assert_allclose(f[['X1','X2','X3','X4']],s.states)
    assert np.all(np.diff(s.dates)==np.timedelta64(1,'h'))

@pytest.mark.parametrize('index',[-1,True,1.5,5489])
def test_invalid_snapshot(data,index):
    with pytest.raises(ValueError): snapshot(data.get('principal','E0'),index)

@pytest.mark.parametrize('speed',[1,6,24,72,168])
def test_clock_speed_pause_end(speed):
    p=PlayerState(speed=speed)
    p.play(100.,1000);p.tick(101.,1000)
    assert p.index==speed
    p.pause();p.tick(300.,1000);assert p.index==speed
    p.play(400.,1000);p.tick(401.,1000);assert p.index==2*speed
    p.seek(999);p.play(500.,1000);p.tick(502.,1000)
    assert p.index==1000 and not p.playing
    p.play(600.,1000);assert not p.playing

def test_fractional_clock_and_context():
    p=PlayerState(speed=1);p.play(0,744)
    assert p.tick(.4,744)==0 and p.tick(1.1,744)==1
    p.context('principal','E1');assert p.index==1 and not p.playing
    p.context('sensibilidad_enero','E1');assert p.index==0
    with pytest.raises(ValueError): p.set_speed(2,2,744)

def test_custom_is_separate_and_read_only(data):
    before=file_signature(ROOT)
    s=data.get('sensibilidad_enero','E0')
    custom=custom_experiment(s,s.parameters)
    assert custom.custom and custom.code=='Personalizado'
    np.testing.assert_array_equal(custom.states,s.states)
    assert file_signature(ROOT)==before

@pytest.mark.parametrize('page',['overview','simulation','scenarios_view','validation_view','methodology'])
def test_pages_load(page):
    at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
    if page!='overview': at.switch_page(f'app_pages/{page}.py').run()
    assert not at.exception

def test_player_widgets_and_windows():
    at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
    at.switch_page('app_pages/simulation.py').run()
    at.button(key='next_hour').click().run()
    assert at.session_state.player.index==1
    at.slider(key='time_index').set_value(5488).run()
    assert at.session_state.player.index==5488 and at.button(key='play').disabled
    at.button(key='reset').click().run()
    assert at.slider(key='time_index').value==0
    at.selectbox(key='window').select('sensibilidad_enero').run()
    assert at.slider(key='time_index').max==744 and not at.exception

def test_custom_requires_submit():
    at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
    at.selectbox(key='window').select('sensibilidad_enero').run()
    at.switch_page('app_pages/simulation.py').run()
    at.segmented_control(key='source').set_value('Personalizado').run()
    assert 'custom_result' not in at.session_state
    at.button(key='run_custom').click().run()
    assert at.session_state.custom_result.custom and not at.exception
