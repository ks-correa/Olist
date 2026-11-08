"""Drive a localhost Streamlit agent API and retain observable evidence."""
from pathlib import Path
import json
import urllib.request

OUT=Path(__file__).resolve().parents[1]/'reports/modelo_v2'
URL='http://127.0.0.1:8503/_stcore/agent/'


def post(body):
    request=urllib.request.Request(URL+'interact',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
    return json.load(urllib.request.urlopen(request,timeout=45))


if __name__=='__main__':
    schema=json.load(urllib.request.urlopen(URL+'openapi.json'))
    r=post({'page':'modelo-v2'});sid=r['session_id'];output=[]
    def check(result,request):
        assert result['status']=='ready',result
        exceptions=[]
        def visit(node):
            if node.get('type')=='exception':exceptions.append(node)
            for child in node.get('children',[]):visit(child)
        visit(result['tree']);assert not exceptions,exceptions
        output.append(dict(request=request,status=result['status'],actions=result.get('actions')))
    check(r,{'page':'modelo-v2'})
    for state in [{'v2_hour':5488},{'v2_version':'Modelo original V1'},{'v2_scope':'Entrenamiento'},{'v2_hour':12803},{'v2_stage':'X4'}]:
        r=post({'session_id':sid,'widget_state':state});check(r,state)
    (OUT/'api_verificacion.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf8')
    print(f'{len(output)} interacciones: ready, sin excepciones')
