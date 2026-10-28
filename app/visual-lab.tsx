'use client';
import {useEffect,useRef,useState} from 'react';
import {courses,type Lesson} from './curriculum';
import examples from './visual-examples.json';
import './visual-lab.css';
type Value = null|string|number|boolean|{kind:string;[key:string]:unknown};
type Frame = {line:number;scope:string;event:string;values:Record<string,Value>;output:string;returned?:Value;exception?:string};
type Trace = {frames:Frame[];output:string;error:string|null;descriptions:Record<string,string>;truncated:boolean;events:number};
const demos:Record<string,{code:string;input:string}>=examples;

function ValueView({value}:{value:Value}) {
  if(value===null||typeof value!=='object')return <span className="vl-primitive">{value===null?'None':typeof value==='boolean'?(value?'True':'False'):typeof value==='string'?JSON.stringify(value):String(value)}</span>;
  if(value.kind==='table'){
    const columns=value.columns as string[],rows=value.rows as Value[][];
    return <div className="vl-table-wrap"><table><thead><tr>{columns.map((name,i)=><th key={i} scope="col">{name}</th>)}</tr></thead><tbody>{rows.map((row,i)=><tr key={i}>{row.map((cell,j)=><td key={j}><ValueView value={cell}/></td>)}</tr>)}</tbody></table>{Array.isArray(value.shape)&&<small>Shape: {(value.shape as number[]).join(' × ')} · preview limited to 8 rows/columns</small>}</div>;
  }
  if(value.kind==='database')return <>{(value.tables as {name:string;kind:string;columns:string[];rows:Value[][]}[]).map(table=><div key={table.name}><b>{table.name}</b><ValueView value={table}/></div>)}<small>Synthetic in-memory SQLite tables · up to 4 tables / 8 rows shown</small></>;
  if(value.kind==='dict')return <div className="vl-dict">{(value.entries as [string,Value][]).map(([key,item])=><div key={key}><b>{key}</b><ValueView value={item}/></div>)}<small>{String(value.size)} keys · first 12 shown</small></div>;
  if(value.kind==='array')return <><small>NumPy shape: {(value.shape as number[]).join(' × ')}</small><ValueView value={value.items as Value}/></>;
  if(Array.isArray(value.items))return <><div className="vl-items">{(value.items as Value[]).map((item,i)=><div key={i}><small>{i}</small><ValueView value={item}/></div>)}</div><small>{value.kind==='set'||value.kind==='frozenset'?'Set members shown sorted for readability; a set has no positional order.':`${String(value.size)} items · first 12 shown; labels are positions in this preview.`}</small></>;
  return <span className="vl-primitive">{String(value.text||value.kind)}</span>;
}

function Experiment({lesson,onPractice,assetBase}:{lesson:Lesson;onPractice:(lesson:Lesson)=>void;assetBase:string}) {
  const initial=demos[lesson.id];
  const [code,setCode]=useState(initial.code),[input,setInput]=useState(initial.input);
  const [prediction,setPrediction]=useState(''),[committed,setCommitted]=useState(false);
  const [result,setResult]=useState<Trace|null>(null),[step,setStep]=useState(0);
  const [busy,setBusy]=useState(false),[status,setStatus]=useState('Predict the output, then run the experiment.');
  const worker=useRef<Worker|null>(null),timer=useRef<ReturnType<typeof setTimeout>|null>(null);
  const draftKey='pythonquest-visual-draft-v1-'+lesson.id;
  const [loaded,setLoaded]=useState(false);
  useEffect(()=>{try{const saved=JSON.parse(localStorage.getItem(draftKey)||'null');if(saved&&typeof saved==='object'){if(typeof saved.code==='string'&&saved.code.length<=50000)setCode(saved.code);if(typeof saved.input==='string'&&saved.input.length<=10000)setInput(saved.input);if(typeof saved.prediction==='string')setPrediction(saved.prediction.slice(0,3000));}}catch{}setLoaded(true);},[draftKey]);
  useEffect(()=>{if(loaded){try{localStorage.setItem(draftKey,JSON.stringify({code,input,prediction}));}catch{}}},[loaded,draftKey,code,input,prediction]);
  function cleanup(){worker.current?.terminate();worker.current=null;if(timer.current)clearTimeout(timer.current);timer.current=null;}
  useEffect(()=>()=>cleanup(),[]);
  function invalidate(){setResult(null);setCommitted(false);setStep(0);setStatus('The experiment changed. Predict again before running.');}
  function run(){
    if(busy||!committed)return;
    cleanup();setBusy(true);setResult(null);setStep(0);setStatus('Loading Python… first use needs internet.');
    const deadline=(ms:number)=>{if(timer.current)clearTimeout(timer.current);timer.current=setTimeout(()=>{cleanup();setBusy(false);setStatus('Time limit reached. Reduce the input or check for an endless loop, then retry.');},ms);};
    try{
      const active=new Worker(assetBase+'visual-worker.js',{type:'module'});worker.current=active;deadline(180000);
      active.onmessage=({data})=>{
        if(worker.current!==active)return;
        if(data.type==='loading'){setStatus(data.message);return;}
        if(data.type==='ready'){setStatus('Tracing real Python execution…');deadline(15000);return;}
        if(data.type==='result'){setResult(data as Trace);setStatus(data.error?'The experiment raised an error. Inspect the trace and last message.':'Experiment complete. Step through the snapshots and compare your prediction.');}
        else setStatus(data.error||'The experiment could not run.');
        setBusy(false);cleanup();
      };
      active.onerror=()=>{if(worker.current!==active)return;cleanup();setBusy(false);setStatus('Could not load the visual runtime. Check your connection and retry.');};
      active.postMessage({code,input});
    }catch(error){cleanup();setBusy(false);setStatus(String(error));}
  }
  const frame=result?.frames[step];
  const prior=frame?result?.frames.slice(0,step).reverse().find(item=>item.scope===frame.scope):null;
  return <div className="vl-experiment">
    <section className="vl-card"><span className="eyebrow">01 · UNDERSTAND & PREDICT</span><h2>{lesson.title}</h2><p>{lesson.summary}</p>{lesson.theory.split('\n\n').map((paragraph,i)=><p key={i}>{paragraph}</p>)}<p className="vl-note">This lab begins with a worked example. Your original practice exercise and saved work are separate.</p><label htmlFor="vl-prediction">What will this code print? Explain your reasoning.</label><textarea id="vl-prediction" value={prediction} maxLength={3000} readOnly={busy||committed} onChange={e=>setPrediction(e.target.value)} placeholder="Predict the values, order, and any error before you run."/><button className="secondary" disabled={busy||!prediction.trim()} onClick={()=>setCommitted(!committed)}>{committed?'Edit my prediction':'Commit my prediction'}</button>{committed&&<p role="status">Prediction recorded for this experiment. Now run it and compare; this is reflection, not a graded answer.</p>}</section>
    <section className="vl-card"><span className="eyebrow">02 · CHANGE ONE THING & RUN</span><label htmlFor="vl-code">Worked Python example · editable</label><textarea id="vl-code" className="vl-editor" value={code} maxLength={50000} readOnly={busy} spellCheck={false} autoCapitalize="off" autoCorrect="off" onChange={e=>{setCode(e.target.value);invalidate();}}/><label htmlFor="vl-input">Program input · one answer per line</label><textarea id="vl-input" value={input} maxLength={10000} readOnly={busy} onChange={e=>{setInput(e.target.value);invalidate();}}/><div className="vl-actions"><button className="primary" disabled={busy||!committed||!code.trim()} onClick={run}>Run visual experiment</button><button className="secondary" disabled={!busy} onClick={()=>{cleanup();setBusy(false);setStatus('Stopped. Your visual draft is still here.');}}>Stop</button><button className="secondary" disabled={busy} onClick={()=>{if(code!==initial.code&&!window.confirm('Replace this visual draft with the worked example?'))return;setCode(initial.code);setInput(initial.input);invalidate();}}>Reset example</button></div><p role="status" aria-live="polite">{status}</p></section>
    {result&&<section className="vl-card"><span className="eyebrow">03 · FOLLOW THE EXECUTION</span><h2>See what Python actually did</h2><p>Line snapshots show state <b>before</b> the highlighted line executes. Move forward to see its effect. Function-return events show the returned value.</p>{frame&&<><div className="vl-actions"><button className="secondary" disabled={step===0} onClick={()=>setStep(step-1)}>← Previous step</button><b>Step {step+1} / {result.frames.length}</b><button className="secondary" disabled={step===result.frames.length-1} onClick={()=>setStep(step+1)}>Next step →</button></div><label htmlFor="vl-step">Execution position</label><input id="vl-step" type="range" min={0} max={Math.max(0,result.frames.length-1)} value={step} onChange={e=>setStep(Number(e.target.value))}/><div className="vl-trace-grid"><div><div className="vl-source" aria-label="Code with current execution line">{code.split('\n').map((line,i)=><div className={frame.line===i+1?'vl-current':''} key={i}><span>{i+1}</span><code>{line||' '}</code></div>)}</div><div className="vl-explanation"><b>{frame.event==='line'?'Before':frame.event==='return'?'Returning from':'Exception at'} line {frame.line} · {frame.scope}</b><p>{result.descriptions[String(frame.line)]||'Inspect this execution event and the visible state.'}</p>{frame.event==='return'&&<><h3>Returned value</h3><ValueView value={frame.returned??null}/></>}{frame.exception&&<p className="vl-error">{frame.exception}</p>}</div></div><div><h3>Visible variables</h3><p className="vl-note">Changed values are highlighted relative to the preceding snapshot in this scope. Up to 12 names are shown.</p><div className="vl-values">{Object.entries(frame.values).map(([name,value])=><div className={JSON.stringify(prior?.values[name])!==JSON.stringify(value)?'vl-value vl-changed':'vl-value'} key={name}><h4>{name}</h4><ValueView value={value}/></div>)}</div>{!Object.keys(frame.values).length&&<p>No user variables have been bound in this scope yet.</p>}<h3>Output at this step</h3><pre className="vl-output">{frame.output||'(Nothing printed yet.)'}</pre></div></div></>}{result.truncated&&<p className="vl-note">The first 240 execution events are shown. Later events were omitted; the output below shows what was captured.</p>}<h3>Actual final output</h3><pre className="vl-output">{result.output||'(No printed output.)'}</pre>{result.error&&<pre className="vl-error" role="alert">{result.error}</pre>}<h3>Your prediction</h3><p className="vl-prediction">{prediction}</p><p>Which line explains any difference? Change one value or condition above, make a fresh prediction, and run again. This trace shows Python statements; it does not expose the internal C operations of NumPy, pandas, or SQLite.</p></section>}
    <section className="vl-card"><span className="eyebrow">04 · APPLY IT INDEPENDENTLY</span><h2>Now solve the original challenge</h2><p>{lesson.task}</p><button className="primary" onClick={()=>onPractice(lesson)}>Open original practice exercise →</button><p className="vl-note">Visual drafts save only in this browser. Lab runs do not award XP, submit answers, or change practice completion.</p></section>
  </div>;
}

export default function VisualLab({onPractice,assetBase='/'}:{onPractice:(lesson:Lesson)=>void;assetBase?:string}) {
  const [courseId,setCourseId]=useState(courses[0].id),[lessonId,setLessonId]=useState(courses[0].lessons[0].id),[search,setSearch]=useState('');
  const course=courses.find(item=>item.id===courseId)!;
  const lesson=course.lessons.find(item=>item.id===lessonId)||course.lessons[0];
  const index=course.lessons.indexOf(lesson);
  const matches=course.lessons.filter(item=>(item.title+' '+item.summary).toLowerCase().includes(search.toLowerCase()));
  return <div className="visual-lab"><div className="page-heading"><div><div className="eyebrow">VISUAL LAB · ALL {courses.flatMap(item=>item.lessons).length} LESSONS</div><h1>Make the code visible<span>.</span></h1><p>Predict → explore → inspect → practice. A separate way to understand the same Python journey.</p></div></div><div className="vl-layout"><aside className="vl-nav"><label htmlFor="vl-course">Choose a course</label><select id="vl-course" value={courseId} onChange={e=>{setCourseId(e.target.value);setLessonId(courses.find(item=>item.id===e.target.value)!.lessons[0].id);setSearch('');}}>{courses.map(item=><option key={item.id} value={item.id}>{item.title} · {item.lessons.length} lessons</option>)}</select><label htmlFor="vl-search">Find a visual lesson</label><input id="vl-search" value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search this course…"/>{matches.map(item=><button className={lesson.id===item.id?'selected':''} aria-current={lesson.id===item.id?'page':undefined} key={item.id} onClick={()=>setLessonId(item.id)}>{String(course.lessons.indexOf(item)+1).padStart(2,'0')} · {item.title}</button>)}{!matches.length&&<p>No matching lessons in this course.</p>}</aside><div><Experiment key={lesson.id} lesson={lesson} onPractice={onPractice} assetBase={assetBase}/><div className="vl-actions vl-pagination"><button className="secondary" disabled={index===0} onClick={()=>setLessonId(course.lessons[index-1].id)}>← Previous lesson</button><span>{index+1} / {course.lessons.length}</span><button className="secondary" disabled={index===course.lessons.length-1} onClick={()=>setLessonId(course.lessons[index+1].id)}>Next lesson →</button></div></div></div></div>;
}
