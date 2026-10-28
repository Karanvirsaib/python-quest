import contextlib
import io
import json
import runpy
from pathlib import Path

root=Path(__file__).resolve().parent.parent
engine=runpy.run_path(str(root/'public/visual-engine.py'))['trace_program']
courses=json.loads((root/'app/curriculum.json').read_text(encoding='utf-8'))
examples=json.loads((root/'app/visual-examples.json').read_text(encoding='utf-8'))
lessons=[lesson for course in courses for lesson in course['lessons']]
assert set(examples)=={lesson['id'] for lesson in lessons}
for lesson in lessons:
    example=examples[lesson['id']]
    trace=engine(example['code'],example['input'])
    assert trace['error'] is None,(lesson['id'],trace['error'])
    assert trace['frames'],lesson['id']
    assert trace['output'].strip(),lesson['id']
    assert len(trace['frames'])<=240
    assert all(1<=frame['line']<=len(example['code'].splitlines()) for frame in trace['frames'])
    values=iter(example['input'].split('\n'))
    output=io.StringIO()
    with contextlib.redirect_stdout(output):
        exec(example['code'],{'input':lambda *a:next(values)})
    assert trace['output']==output.getvalue(),lesson['id']
    json.dumps(trace,allow_nan=False)
print(f"PASS: all {len(lessons)} visual examples trace successfully and match real untraced Python output.")
loop=engine('total=0\nfor n in [1,2,3]:\n    total+=n\nprint(total)')
assert loop['output']=='6\n'
assert loop['frames'][0]['values']=={},'Line events must show pre-execution state.'
assert any(frame['values'].get('total')==6 for frame in loop['frames'])
assert engine('x=1/0')['error'].startswith('ZeroDivisionError')
assert engine('def bad(:')['error'].startswith('SyntaxError')
assert engine('while True:\n    pass')['error'].startswith('RuntimeError')
assert engine('for i in range(300):\n    value=i')['truncated'] is True
assert engine('print("x"*21000)')['error'].startswith('RuntimeError')
print('PASS: pre-line state, loops, errors, event/output bounds, and truncation checks.')
