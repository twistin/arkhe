"""Fusión de rangos semánticos y BM25 sobre el corpus ya autorizado."""
from collections import Counter
import math
import re
import unicodedata

STOP=set('the a an of in on to and or is are what how explain definition concept de la el los las un una que es explica como y en del for with'.split())
def tokens(text):
    text=re.sub(r'-\s*\n\s*','',text.lower())
    text=''.join(c for c in unicodedata.normalize('NFKD',text) if not unicodedata.combining(c))
    return [t for t in re.findall(r'\w+',text) if len(t)>2 and t not in STOP]

def hybrid(rows, rankings, queries, top_k):
    if not rows: return []
    counts={r['id']:Counter(tokens(r['text'])) for r in rows}
    lengths={k:sum(v.values()) for k,v in counts.items()}
    avg=sum(lengths.values())/len(rows) or 1
    df=Counter(t for count in counts.values() for t in count)
    lists=list(rankings)
    for query in queries:
        terms=set(tokens(query));scores={}
        for key,count in counts.items():
            score=0
            for term in terms:
                tf=count[term]
                if tf:
                    idf=math.log(1+(len(rows)-df[term]+.5)/(df[term]+.5))
                    score+=idf*tf*2.2/(tf+1.2*(.25+.75*lengths[key]/avg))
            if score: scores[key]=score
        lists.append(sorted(scores,key=lambda k:(-scores[k],k))[:60])
    fused=Counter()
    for ranking in lists:
        for rank,key in enumerate(ranking[:60],1): fused[key]+=1/(60+rank)
    by_id={r['id']:r for r in rows}
    ordered=sorted(fused,key=lambda k:(-fused[k],k))
    # One anchor per page first; repeated overlapping chunks cannot crowd out context.
    selected=[];deferred=[];seen=set()
    for key in ordered:
        row=by_id[key];page=(row['version_id'],row['segment_id'])
        (deferred if page in seen else selected).append(row)
        seen.add(page)
    return (selected+deferred)[:top_k]
