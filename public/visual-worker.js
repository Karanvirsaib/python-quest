import { loadPyodide } from 'https://cdn.jsdelivr.net/pyodide/v314.0.7/full/pyodide.mjs';
const ready = loadPyodide({indexURL:'https://cdn.jsdelivr.net/pyodide/v314.0.7/full/'});
const engine = fetch(new URL('./visual-engine.py',import.meta.url)).then(response=>{if(!response.ok)throw new Error('Visual engine could not load.');return response.text();});
self.onmessage=async ({data})=>{
  let globals;
  try{
    if(typeof data.code!=='string'||data.code.length>50000)throw new Error('Keep the teaching example under 50,000 characters.');
    const py=await ready;
    self.postMessage({type:'loading',message:'Preparing Python packages…'});
    await py.loadPackagesFromImports(data.code);
    globals=py.toPy({_visual_source:data.code,_visual_input:data.input||''});
    self.postMessage({type:'ready'});
    await py.runPythonAsync(await engine,{globals});
    self.postMessage({type:'result',...JSON.parse(globals.get('_visual_result'))});
  }catch(error){self.postMessage({type:'error',error:String(error)});}
  finally{globals?.destroy();}
};
