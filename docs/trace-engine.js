// Independent explicit-set product traversal, not generated Python output.
import {validate} from './engine.js';
export function auditTraces(data) {
 if(!data||typeof data!=='object'||Array.isArray(data)||Object.keys(data).sort().join()!=='pair,system')throw Error('Expected exactly system and pair');
 const system=validate(data.system),{states,actions,edges}=system;
 if(!Array.isArray(data.pair)||data.pair.length!==2||data.pair.some(s=>typeof s!=='string'||!states.includes(s)))throw Error('pair: two declared states');
 const input={system,pair:[...data.pair]},queue=[data.pair.map(p=>[p])],ids=new Map([[JSON.stringify(queue[0]),0]]),parents=[null],vias=[null],depths=[0],nodes=[];
 const step=(group,a)=>states.filter(q=>edges.some(([p,b,t])=>group.includes(p)&&a===b&&q===t));
 for(let i=0;i<queue.length;i++) {
  const [left,right]=queue[i],next=[];
  for(const a of actions) {
   const target=[step(left,a),step(right,a)],k=JSON.stringify(target);
   if(!ids.has(k)){ids.set(k,queue.length);queue.push(target);parents.push(i);vias.push(a);depths.push(depths[i]+1);}
   next.push(ids.get(k));
  }
  nodes.push({id:i,left,right,parent:parents[i],via:vias[i],depth:depths[i],mismatch:Boolean(left.length)!==Boolean(right.length),next});
 }
 const mismatches=nodes.filter(n=>n.mismatch).map(n=>n.id),first_mismatch=mismatches[0]??null,path=[];
 let word=null;
 if(first_mismatch!==null){for(let i=first_mismatch;i!==null;i=parents[i])path.unshift(i);word=path.slice(1).map(i=>vias[i]);}
 const layers=Array.from({length:Math.max(...depths)+1},(_,k)=>nodes.filter(n=>n.depth===k).map(n=>n.id));
 return {schema:'bisimlab-traces-v1',input,nodes,layers,mismatches,equivalent:!mismatches.length,first_mismatch,path,word};
}
