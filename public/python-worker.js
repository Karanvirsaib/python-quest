import { loadPyodide } from 'https://cdn.jsdelivr.net/pyodide/v314.0.7/full/pyodide.mjs';
const ready = loadPyodide({ indexURL: 'https://cdn.jsdelivr.net/pyodide/v314.0.7/full/' });
self.onmessage = async ({data}) => {
  let globals;
  try {
    const py = await ready;
    self.postMessage({ type: 'loading', message: 'Preparing Python packages… first-time data libraries may take a moment.' });
    await py.loadPackagesFromImports(data.code + '\n' + (data.tests || ''));
    self.postMessage({ type: 'ready' });
    let output = '';
    py.setStdout({batched: text => { output += text + '\n'; if (output.length > 20000) throw new Error('Output limit reached. Try a smaller loop.'); }});
    py.setStderr({batched: text => { output += text + '\n'; }});
    const lines = (data.input || '').split('\n');
    let index = 0;
    py.setStdin({stdin: () => index < lines.length ? lines[index++] : null});
    globals = py.toPy({ __name__: '__main__', _quest_input: data.input || '', _quest_source: data.code });
    await py.runPythonAsync(data.code, { globals });
    let passed = false, feedback = '';
    if (data.tests) {
      globals.set('_quest_output', output.trim());
      try { await py.runPythonAsync(data.tests, { globals }); passed = true; }
      catch (error) { feedback = error.message.split('\n').filter(Boolean).slice(-1)[0]; }
    }
    self.postMessage({type:'result', output, passed, feedback});
  } catch (error) { self.postMessage({type:'error', error:error.message}); }
  finally { globals?.destroy(); }
};
