import json, io, contextlib, ast
from pathlib import Path
data = json.loads((Path(__file__).parent.parent / 'app' / 'curriculum.json').read_text(encoding='utf-8'))
count = 0
failures = []
mutations = 0
for course in data:
    for lesson in course['lessons']:
        try:
            compile(lesson['starter'],lesson['id']+' starter','exec')
            values = iter(lesson['input'].split('\n'))
            ns = {'input': lambda *a: next(values), '_quest_input': lesson['input'], '_quest_source': lesson['solution']}
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exec(lesson['solution'], ns)
            ns['_quest_output'] = output.getvalue().strip()
            exec(lesson['tests'], ns)
            if 'packages' in lesson:
                function = next(n.name for n in ast.parse(lesson['solution']).body if isinstance(n,ast.FunctionDef))
                ns[function] = lambda *args, **kwargs: None
                try:
                    exec(lesson['tests'],ns)
                except Exception:
                    mutations += 1
                else:
                    raise AssertionError('Exercise checks accepted a no-op implementation.')
            count += 1
        except Exception as exc:
            failures.append((lesson['id'],repr(exc)))
print(f'{count} lesson solutions passed all exercise checks.')
print(f'{mutations} new exercise check suites rejected no-op implementations.')
for lesson_id,error in failures: print(f'FAIL {lesson_id}: {error}')
if failures: raise SystemExit(1)
