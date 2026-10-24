import json, io, contextlib
from pathlib import Path
data = json.loads((Path(__file__).parent.parent / 'app' / 'curriculum.json').read_text(encoding='utf-8'))
count = 0
for course in data:
    for lesson in course['lessons']:
        values = iter(lesson['input'].split('\n'))
        ns = {'input': lambda *a: next(values), '_quest_input': lesson['input'], '_quest_source': lesson['solution']}
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exec(lesson['solution'], ns)
        ns['_quest_output'] = output.getvalue().strip()
        exec(lesson['tests'], ns)
        count += 1
print(f'{count} lesson solutions passed all exercise checks.')
