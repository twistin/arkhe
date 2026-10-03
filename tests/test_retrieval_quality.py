from docente_ai.rag.ranking import hybrid, tokens

def row(id,text,page=None):
    return {'id':id,'text':text,'version_id':'v','segment_id':page or id}

def test_lexical_evidence_can_recover_beyond_semantic_shortlist():
    rows=[row('noise','Computers and spectral sound.'),row('definition','Isorhythm repeats a rhythmic talea in the tenor.')]
    result=hybrid(rows,[['noise','definition']],['isorhythm talea tenor'],2)
    assert result[0]['id']=='definition'

def test_overlapping_pages_do_not_crowd_out_complementary_passages():
    rows=[row('a','tenor talea','one'),row('b','tenor talea','one'),row('c','color melody','two')]
    result=hybrid(rows,[['a','b','c']],['tenor talea color melody'],2)
    assert len({r['segment_id'] for r in result})==2

def test_tokenization_handles_accents_and_line_hyphenation():
    assert 'isorritmico' in tokens('isorrítmico')
    assert 'rhythmic' in tokens('rhyth-\nmic')

def test_no_lexical_hits_does_not_invent_candidates():
    assert hybrid([],[],['motet'],6)==[]

def test_full_passage_reranking_rejects_mentions_and_reads_every_candidate(monkeypatch):
    import json
    from docente_ai.rag.planning import rerank
    from docente_ai.llm.generation import OllamaGenerator
    from docente_ai.generation.settings import GenerationSettings
    examined=[]
    residency=[]
    monkeypatch.setattr(OllamaGenerator,'__enter__',lambda self:self)
    monkeypatch.setattr(OllamaGenerator,'__exit__',lambda self,*args:self.client.close())
    def generate(self,messages):
        items=json.loads(messages[-1]['content'])['passages'];examined.extend(items)
        residency.append(self.keep_alive)
        return {'content':json.dumps({'scores':[{'id':p['id'],'score':3 if 'definition' in p['text'] else 1} for p in items]})}
    monkeypatch.setattr(OllamaGenerator,'generate',generate)
    candidates=[{'chunk_id':str(i),'text':('definition ' if i==9 else 'mention ')+('x'*1100)} for i in range(12)]
    result,audit=rerank('concept',candidates,GenerationSettings('fake:1'))
    assert [r['chunk_id'] for r in result]==['9']
    assert [p['text'] for p in examined]==[c['text'] for c in candidates]
    assert audit['batches']>1
    assert residency[-1]==0 and all(x=='5m' for x in residency[:-1])

def test_final_order_uses_only_candidates_that_pass_relevance(monkeypatch):
    import json
    from docente_ai.rag.planning import rerank
    from docente_ai.llm.generation import OllamaGenerator
    from docente_ai.generation.settings import GenerationSettings
    monkeypatch.setattr(OllamaGenerator,'__enter__',lambda self:self)
    monkeypatch.setattr(OllamaGenerator,'__exit__',lambda self,*args:self.client.close())
    def generate(self,messages):
        if 'Score EVERY' in messages[0]['content']:
            return {'content':json.dumps({'scores':[{'id':0,'score':2},{'id':1,'score':0},{'id':2,'score':3}]})}
        supplied=json.loads(messages[-1]['content'])['passages']
        assert {p['id'] for p in supplied}=={0,2}
        return {'content':'{"ids":[2,0]}'}
    monkeypatch.setattr(OllamaGenerator,'generate',generate)
    result,_=rerank('concept',[{'chunk_id':str(i),'text':f'Passage {i}.'} for i in range(3)],GenerationSettings('fake:1'))
    assert [r['chunk_id'] for r in result]==['2','0']


def test_final_selector_is_completed_for_multi_topic_coverage(monkeypatch):
    import json
    from docente_ai.rag.planning import rerank
    from docente_ai.llm.generation import OllamaGenerator
    from docente_ai.generation.settings import GenerationSettings
    monkeypatch.setattr(OllamaGenerator,'__enter__',lambda self:self)
    monkeypatch.setattr(OllamaGenerator,'__exit__',lambda self,*args:self.client.close())
    def generate(self,messages):
        if 'Score EVERY' in messages[0]['content']:
            passages=json.loads(messages[-1]['content'])['passages']
            return {'content':json.dumps({'scores':[{'id':p['id'],'score':2} for p in passages]})}
        return {'content':'{"ids":[3,1]}' }
    monkeypatch.setattr(OllamaGenerator,'generate',generate)
    candidates=[{'chunk_id':str(i),'text':f'Subtema {i}.'} for i in range(6)]
    result,_=rerank('consulta con varios subtemas',candidates,GenerationSettings('fake:1'),limit=6)
    assert [r['chunk_id'] for r in result]==['3','1','0','2','4','5']
