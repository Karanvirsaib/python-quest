"""Bounded teaching snapshots from real Python line events, not a simulated interpreter."""
import ast
import contextlib
import io
import json
import math
import sys
import types


def describe_lines(source):
    descriptions = {}
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.stmt):
            continue
        text = {
            'Assign': 'Evaluate the right-hand expression, then bind the result to the name or target on the left.',
            'AnnAssign': 'Compute and assign a value; the annotation describes its intended type.',
            'AugAssign': 'Read the current value, apply the operator, and assign the new value.',
            'FunctionDef': 'Define a function. Its body runs only when that function is called.',
            'Return': 'Evaluate the return expression and send its value back to the caller.',
            'For': 'Take the next item from the iterable and bind the loop variable. Stop when it is exhausted.',
            'While': 'Check the condition before another iteration; a false condition exits the loop.',
            'If': 'Evaluate the condition and choose the matching branch.',
            'Import': 'Load the named module and bind its name for later use.',
            'ImportFrom': 'Import the specified tools from this module.',
            'Expr': 'Evaluate this expression or call. print writes output; other calls may return or change values.',
            'Try': 'Run the protected block; a matching exception selects an except handler.',
            'Raise': 'Raise an exception so the caller or a matching handler can respond.',
            'With': 'Enter the context manager; its exit logic handles cleanup or transaction boundaries.',
            'Continue': 'Skip the remaining statements in this loop iteration.',
            'Break': 'Exit the current loop.',
            'Assert': 'Check this condition and raise AssertionError if it is false.',
            'Delete': 'Remove the named binding or selected item.',
            'Pass': 'Do nothing; this is an explicit empty statement.',
        }.get(type(node).__name__, 'Execute this Python statement; inspect the next snapshot to see its effect.')
        descriptions[str(node.lineno)] = text
    return descriptions


def trace_program(source, program_input=''):
    frames, event_count, truncated = [], 0, False
    output = io.StringIO()
    input_values = iter(program_input.split('\n'))

    def pack(value, depth=0):
        if value is None or isinstance(value, (str, bool, int)):
            return value[:200] if isinstance(value, str) else value
        if isinstance(value, float):
            return value if math.isfinite(value) else str(value)
        if depth > 2:
            return {'kind': 'summary', 'text': type(value).__name__}
        module = type(value).__module__
        if module.startswith('pandas') and hasattr(value, 'to_frame') and not hasattr(value, 'columns'):
            return pack(value.to_frame(), depth)
        if module in ('decimal', 'datetime') or type(value).__name__ in ('Timestamp','Timedelta','NAType','NaTType'):
            return {'kind':'summary','text':type(value).__name__+': '+str(value)[:200]}
        if module.startswith('pandas') and hasattr(value, 'columns'):
            small = value.iloc[:8, :8]
            return {'kind': 'table', 'columns': [str(x) for x in small.columns],
                    'rows': [[pack(x, depth+1) for x in row] for row in small.itertuples(index=False, name=None)],
                    'index': [str(x) for x in small.index], 'shape': list(value.shape)}
        if module.startswith('numpy') and hasattr(value, 'tolist'):
            if value.ndim == 0:
                return pack(value.item(), depth+1)
            small = value[:8] if value.ndim < 2 else value[:8, :8]
            return {'kind': 'array', 'shape': list(value.shape), 'items': pack(small.tolist(), depth+1)}
        if isinstance(value, (list, tuple, set, frozenset)):
            items = list(value)
            if isinstance(value, (set, frozenset)):
                items.sort(key=repr)
            if items and all(isinstance(row, dict) for row in items[:8]):
                columns = list(dict.fromkeys(k for row in items[:8] for k in row))[:8]
                return {'kind':'table','columns':[str(k) for k in columns],
                        'rows':[[pack(row.get(k),depth+1) for k in columns] for row in items[:8]],'shape':[len(items),len(columns)]}
            return {'kind':type(value).__name__, 'items':[pack(v,depth+1) for v in items[:12]], 'size':len(items)}
        if isinstance(value, dict):
            return {'kind':'dict','entries':[[str(k),pack(v,depth+1)] for k,v in list(value.items())[:12]],'size':len(value)}
        if module == 'sqlite3' and type(value).__name__ == 'Connection':
            tables = []
            for (name,) in value.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name LIMIT 4"):
                cursor = value.execute('SELECT * FROM "'+name.replace('"','""')+'" LIMIT 8')
                tables.append({'name':name,'kind':'table','columns':[col[0] for col in cursor.description],
                               'rows':[[pack(v,depth+1) for v in row] for row in cursor.fetchall()]})
            return {'kind':'database','tables':tables}
        if isinstance(value, types.FunctionType):
            return {'kind':'summary','text':'function '+value.__name__}
        if isinstance(value, types.ModuleType):
            return {'kind':'summary','text':'module '+value.__name__}
        return {'kind':'summary','text':type(value).__name__}

    def snapshot(local_values):
        visible = [(key,val) for key,val in local_values.items() if not key.startswith('_') and key != 'input']
        values = {}
        for key,val in visible[:12]:
            try:
                values[key] = pack(val)
            except Exception:
                values[key] = {'kind':'summary','text':type(val).__name__+' (snapshot unavailable)'}
        return values

    def trace(frame, event, arg):
        nonlocal event_count, truncated
        if frame.f_code.co_filename != 'visual_lesson.py':
            return None
        if event in ('line','return','exception'):
            event_count += 1
            if event_count > 10000:
                raise RuntimeError('Teaching trace exceeded 10,000 events. Reduce the input or fix the loop.')
            if len(frames) < 240:
                step = {'line':frame.f_lineno,'scope':frame.f_code.co_name,'event':event,
                        'values':snapshot(frame.f_locals),'output':output.getvalue()[-10000:]}
                if event == 'return':
                    step['returned'] = pack(arg)
                if event == 'exception':
                    step['exception'] = type(arg[1]).__name__+': '+str(arg[1])[:300]
                frames.append(step)
            else:
                truncated = True
        if output.tell() > 20000:
            raise RuntimeError('Teaching output exceeded 20,000 characters.')
        return trace

    scope = {'__name__':'__main__','input':lambda prompt='':next(input_values)}
    error = None
    previous_trace = sys.gettrace()
    try:
        descriptions = describe_lines(source)
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            sys.settrace(trace)
            exec(compile(source,'visual_lesson.py','exec'),scope)
    except Exception as exc:
        error = type(exc).__name__+': '+str(exc)[:1000]
        descriptions = locals().get('descriptions',{})
    finally:
        sys.settrace(previous_trace)
    return {'frames':frames,'output':output.getvalue()[:20000],'error':error,
            'descriptions':descriptions,'truncated':truncated,'events':event_count}


if '_visual_source' in globals():
    _visual_result = json.dumps(trace_program(_visual_source, _visual_input), allow_nan=False)
