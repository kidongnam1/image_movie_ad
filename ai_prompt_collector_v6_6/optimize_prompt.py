import argparse, importlib.util
from pathlib import Path
HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location('collector',HERE/'collect_and_index.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
ap=argparse.ArgumentParser(description='Create a target-model prompt optimization brief/template without changing the core creative idea.')
ap.add_argument('model')
ap.add_argument('prompt')
ap.add_argument('--use-case',default='general')
a=ap.parse_args(); key=a.model.lower().replace(' ','_').replace('-','_')
alias={'gpt_image':'gpt_image_2','gptimage2':'gpt_image_2','nano_banana_pro':'nano_banana','qwen':'qwen_image_3','ltx':'ltx_video','cogvideo':'cogvideox','hunyuan':'hunyuan_video'}
key=alias.get(key,key)
p=m.MODEL_PROFILES.get(key)
if not p:
    print('Unknown model. Available: '+', '.join(sorted(m.MODEL_PROFILES))); raise SystemExit(2)
print(f'TARGET MODEL: {key}')
print(f'MEDIA: {p["media"]}')
print(f'BEST STRUCTURE: {p["structure"]}')
print(f'STRONG AT: {p["strong_at"]}')
print(f'GUIDANCE: {p["hint"]}')
print('\nOPTIMIZATION BRIEF')
print('Use case:',a.use_case)
print('Core idea to preserve:',a.prompt)
if p['media']=='image':
    print('Rewrite fields: subject / environment / composition / lighting / camera or medium / materials / text & layout / constraints / avoid.')
else:
    print('Rewrite fields: opening state / subject action / camera motion / scene motion / temporal beats / transition or end state / audio-dialogue if relevant.')
print('Rule: preserve factual/product identity; do not invent claims, certifications, counts, labels, or on-image copy not supplied by the user.')
