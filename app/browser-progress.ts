// The GitHub Pages edition deliberately has no server or shared account state.
const KEY = 'python-quest-learning-v1';
type LocalRecord = {lessonId:string;code:string;notes:string;completed:boolean;completedAt:string|null;updatedAt:string};
type State = {records:LocalRecord[];profile:{name:string;goal:number}};
export async function browserProgress(_url:string, options?:RequestInit):Promise<Response> {
  try {
    const raw=localStorage.getItem(KEY);
    const state:State=raw?JSON.parse(raw):{records:[],profile:{name:'Explorer',goal:1}};
    if(!Array.isArray(state.records)||!state.profile)throw new Error('Stored profile is invalid.');
    if(options?.method==='PUT') {
      const body=JSON.parse(String(options.body));
      if(body.profile) state.profile=body.profile;
      else {
        const previous=state.records.find(r=>r.lessonId===body.lessonId);
        const record={...body,completed:body.completed||!!previous?.completed,completedAt:previous?.completedAt||body.completedAt};
        state.records=state.records.filter(r=>r.lessonId!==record.lessonId).concat(record);
      }
      localStorage.setItem(KEY,JSON.stringify(state));
      return Response.json({ok:true});
    }
    return Response.json(state);
  } catch {
    return Response.json({error:'Browser storage is unavailable or full. Enable site storage or try a normal browser window. Your unsaved code is still in the editor.'},{status:503});
  }
}
