export function validate(data){
 const keys=(x,k)=>x!==null&&typeof x==='object'&&!Array.isArray(x)&&Object.keys(x).sort().join('|')===k.slice().sort().join('|');
 const symbol=x=>typeof x==='string'&&/^[A-Za-z][A-Za-z0-9_]{0,15}$/.test(x);
 if(!keys(data,['states'])||!Array.isArray(data.states)||data.states.length<1||data.states.length>6)throw Error('input needs exactly one to six states');
 const names=[];
 for(const s of data.states){
  if(!keys(s,['name','owner','safe','moves'])||!symbol(s.name)||names.includes(s.name))throw Error('unique state names and exact state keys required');names.push(s.name);
  if(!['controller','environment'].includes(s.owner)||typeof s.safe!=='boolean'||!Array.isArray(s.moves)||s.moves.length<1||s.moves.length>3)throw Error('each state needs an owner, boolean safe and one to three moves; dead ends rejected');
  const actions=[];for(const m of s.moves){if(!keys(m,['action','to'])||!symbol(m.action)||actions.includes(m.action))throw Error('exact move keys and unique action identifiers required');actions.push(m.action);}
 }
 for(const s of data.states)for(const m of s.moves)if(!names.includes(m.to))throw Error('target must name a declared state');
 return {states:data.states.map(s=>({name:s.name,owner:s.owner,safe:s.safe,moves:s.moves.map(m=>({...m}))}))};
}
export function analyze(input){
 const data=validate(input),states=data.states,names=states.map(s=>s.name),order=xs=>names.filter(n=>xs.has(n));let current=new Set(states.filter(s=>s.safe).map(s=>s.name));
 const ranks=Object.fromEntries(states.map(s=>[s.name,s.safe?null:0])),rounds=[];
 while(true){const after=new Set(),checks=states.map(s=>{const ts=s.moves.map(m=>current.has(m.to)),qualified=s.owner==='controller'?ts.some(Boolean):ts.every(Boolean),kept=s.safe&&qualified;if(kept)after.add(s.name);return {state:s.name,operator:s.owner==='controller'?'exists':'all',safe:s.safe,target_in_before:ts,qualified,kept};});
 const removed=names.filter(n=>current.has(n)&&!after.has(n));rounds.push({index:rounds.length,before:order(current),checks,after:order(after),removed});for(const n of removed)ranks[n]=rounds.length;
 if(names.every(n=>current.has(n)===after.has(n)))break;current=after;
 }
 const records=states.map(s=>{const win=current.has(s.name),moves=s.moves.map(m=>({...m,target_winning:current.has(m.to),target_rank:ranks[m.to],safe_move:win&&s.owner==='controller'&&current.has(m.to),rank_decreasing:ranks[s.name]!==null&&ranks[m.to]!==null&&ranks[m.to]<ranks[s.name]}));return {name:s.name,owner:s.owner,safe:s.safe,winning:win,rank:ranks[s.name],moves,controller_choice:moves.find(m=>m.safe_move)?.action??null,environment_choice:moves.find(m=>s.owner==='environment'&&!win&&s.safe&&m.rank_decreasing)?.action??null};});
 const by=Object.fromEntries(records.map(s=>[s.name,s])),proof_graphs=records.map(root=>{const nodes=[root.name],edges=[];for(let i=0;i<nodes.length;i++){const s=by[nodes[i]];if(!root.winning&&!s.safe)continue;for(const m of s.moves){const selected=root.winning?(s.owner==='environment'||m.action===s.controller_choice):(s.owner==='controller'||m.action===s.environment_choice);if(!selected)continue;edges.push({from:s.name,action:m.action,to:m.to});if(!nodes.includes(m.to))nodes.push(m.to);}}return {start:root.name,kind:root.winning?'closed_invariant':'ranked_counterstrategy',nodes,edges,bad:nodes.filter(n=>!by[n].safe),rank_bound:root.rank};});
 return {schema:'shieldlab-v1',input:data,rounds,winning:order(current),losing:names.filter(n=>!current.has(n)),states:records,proof_graphs};
}
