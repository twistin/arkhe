"""Referencias compactas a extractos literales; ningún texto se reconstruye."""
import re

def passages(text):
    parts=[]
    for sentence in re.split(r'(?<=[.!?])(?=\s)',text):
        while len(sentence)>500:
            end=sentence.rfind(' ',0,500)
            if end<8:end=500
            parts.append(sentence[:end]);sentence=sentence[end:]
        if len(sentence.strip())>=8:parts.append(sentence)
        elif sentence and parts and len(parts[-1]+sentence)<=500:parts[-1]+=sentence
    return [{'id':f'quote_{i:03d}','text':part} for i,part in enumerate(parts,1)]
