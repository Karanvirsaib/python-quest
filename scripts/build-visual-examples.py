"""Create an explicit demonstration for every existing lesson without editing curriculum data."""
import ast
import json
from pathlib import Path

root = Path(__file__).resolve().parent.parent
courses = json.loads((root/'app/curriculum.json').read_text(encoding='utf-8'))
demos = {
    'workshop-errors':"\nprint(safe_int('12'))\nprint(safe_int('bad'))",
    'workshop-modules':'\nprint(distance(3, 4))',
    'workshop-testing':'\nprint(largest([3, 9, 2]))\nprint(largest([]))',
}
examples = {}
for course in courses:
    for lesson in course['lessons']:
        source = lesson['solution']
        if lesson['id'] in demos:
            source += demos[lesson['id']]
        elif course['id'] == 'sql-python':
            # Reuse the real first fixture and query from this lesson's own checks.
            tree = ast.parse(lesson['tests'])
            first_check = next(i for i,n in enumerate(tree.body) if isinstance(n,ast.Assert))
            prefix = '\n'.join(ast.unparse(n) for n in tree.body[:first_check])
            check = tree.body[first_check].test
            assert isinstance(check,ast.Compare)
            source += '\n\n# Tiny synthetic demonstration fixture from the exercise checks.\n'+prefix+'\nresult = '+ast.unparse(check.left)+'\nprint(result)\n'
        assert 'print(' in source,lesson['id']
        examples[lesson['id']] = {'code':source,'input':lesson['input']}
(root/'app/visual-examples.json').write_text(json.dumps(examples,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(f'Prepared {len(examples)} explicit visual examples; original curriculum unchanged.')
