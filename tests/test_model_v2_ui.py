from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).resolve().parents[1]


def test_experiment_ui_versions_and_time():
    at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
    at.switch_page('app_pages/model_v2_view.py').run()
    assert not at.exception
    assert len(at.warning)==1
    at.slider(key='v2_hour').set_value(100).run()
    assert not at.exception and len(at.metric)==4
    at.segmented_control(key='v2_version').set_value('Modelo original V1').run()
    assert not at.exception
    at.segmented_control(key='v2_scope').set_value('Entrenamiento').run()
    at.segmented_control(key='v2_stage').set_value('X4').run()
    assert not at.exception
