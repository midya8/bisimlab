// Independent explicit-set implementation. No Python-generated analysis data.
export function validate(data) {
  if (!data || Array.isArray(data) || typeof data !== 'object' || Object.keys(data).sort().join() !== 'actions,edges,states') throw Error('Expected exactly states, actions, edges');
  for (const [key, lo, hi] of [['states',1,6],['actions',0,3]]) {
    const x=data[key];
    if (!Array.isArray(x)||x.length<lo||x.length>hi||x.some(s=>typeof s!=='string'||!/^[A-Za-z][A-Za-z0-9_]{0,15}$/.test(s))||new Set(x).size!==x.length) throw Error(`${key}: unique short ASCII names; length ${lo}..${hi}`);
  }
  const {states,actions,edges}=data;
  if(!Array.isArray(edges)||edges.length>18) throw Error('At most 18 edge triples');
  const seen=new Set();
  for(const e of edges) {
    if(!Array.isArray(e)||e.length!==3||e.some(x=>typeof x!=='string')||!states.includes(e[0])||!actions.includes(e[1])||!states.includes(e[2])||seen.has(JSON.stringify(e))) throw Error('Unknown name or duplicate/invalid edge');
    seen.add(JSON.stringify(e));
  }
  return structuredClone(data);
}
export function analyze(data) {
  const d=validate(data),{states,actions,edges}=d, key=(p,q)=>JSON.stringify([p,q]);
  const pairs=states.flatMap(p=>states.map(q=>[p,q]));
  let current=new Set(pairs.map(([p,q])=>key(p,q)));
  const rounds=[{index:0,retained:structuredClone(pairs),removed:[]}], specs=[{op:'true'}],depth=[0],ids=new Map();
  const add=(n,z)=>{specs.push(n);depth.push(z);return specs.length-1;};
  for(;;) {
    const removed=[];
    for(const [p,q] of pairs) {
      if(!current.has(key(p,q)))continue;
      const attacks=[];
      for(const [side,source,other] of [['left',p,q],['right',q,p]]) {
        edges.forEach(([s,a,t],i)=>{
          if(s!==source)return;
          const matches=[];
          edges.forEach(([v,b,u],j)=>{if(v===other&&b===a){const pair=side==='left'?[t,u]:[u,t];matches.push({edge:j,pair,survives:current.has(key(...pair))});}});
          attacks.push({side,edge:i,matches,fails:!matches.some(m=>m.survives)});
        });
      }
      const winning=attacks.findIndex(a=>a.fails);
      if(winning>=0)removed.push({pair:[p,q],attacks,winning});
    }
    const pending=[];
    for(const row of removed) {
      const w=row.attacks[row.winning],action=edges[w.edge][1];
      const args=w.matches.map(m=>ids.get(key(...(w.side==='left'?m.pair:[...m.pair].reverse()))));
      const inner=args.length?add({op:'and',args},Math.max(...args.map(i=>depth[i]))):0;
      const diamond=add({op:'diamond',action,arg:inner},depth[inner]+1);
      row.formula=w.side==='left'?diamond:add({op:'not',arg:diamond},depth[diamond]);
      pending.push([key(...row.pair),row.formula]);
    }
    removed.forEach(row=>current.delete(key(...row.pair)));
    rounds.push({index:rounds.length,retained:pairs.filter(p=>current.has(key(...p))),removed});
    pending.forEach(([k,i])=>ids.set(k,i));
    if(!removed.length)break;
  }
  const classes=[];
  for(const p of states) if(!classes.some(c=>c.includes(p)))classes.push(states.filter(q=>current.has(key(p,q))));
  const quotient=[];
  classes.forEach((c,i)=>actions.forEach(a=>classes.forEach((t,j)=>{if(edges.some(([s,b,u])=>c.includes(s)&&b===a&&t.includes(u)))quotient.push([i,a,j]);})));
  const truth=[];
  const formulas=specs.map((n,i)=>{
    let holds;
    if(n.op==='true')holds=[...states];
    else if(n.op==='not')holds=states.filter(s=>!truth[n.arg].includes(s));
    else if(n.op==='and')holds=states.filter(s=>n.args.every(j=>truth[j].includes(s)));
    else holds=states.filter(s=>edges.some(([x,a,t])=>x===s&&a===n.action&&truth[n.arg].includes(t)));
    truth.push(holds);return {...n,depth:depth[i],holds};
  });
  function traces(p,q) {
    const start=[[p],[q]], todo=[[start,[]]], seen=new Set([JSON.stringify(start)]);
    for(let i=0;i<todo.length;i++) {
      const [[left,right],word]=todo[i];
      if(Boolean(left.length)!==Boolean(right.length))return {equivalent:false,word,explored:seen.size};
      for(const a of actions) {
        const next=[left,right].map(group=>states.filter(t=>edges.some(([s,b,u])=>group.includes(s)&&b===a&&u===t)));
        const k=JSON.stringify(next);
        if(!seen.has(k)){seen.add(k);todo.push([next,[...word,a]]);}
      }
    }
    return {equivalent:true,word:null,explored:seen.size};
  }
  return {schema:'bisimlab-v1',input:d,rounds,formulas,pairs:pairs.map(([p,q])=>({pair:[p,q],bisimilar:current.has(key(p,q)),rank:rounds.find(r=>r.removed.some(x=>x.pair[0]===p&&x.pair[1]===q))?.index??null,formula:ids.get(key(p,q))??null,traces:traces(p,q)})),classes,quotient};
}
export function nodeText(n) {
  if(n.op==='true')return 'true';
  if(n.op==='not')return `not F${n.arg}`;
  if(n.op==='and')return n.args.map(i=>`F${i}`).join(' and ');
  return `<${n.action}> F${n.arg}`;
}
