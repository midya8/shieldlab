// Independent strategy-pair simulation, no native reports or generator imports.
import {validateReachAvoid,parseReachAvoidJSON} from './reachavoid-engine.js';
export const validateRecurrence=validateReachAvoid;
export const parseRecurrenceJSON=parseReachAvoidJSON;
function assignments(states){let rows=[[]];for(const s of states)rows=rows.flatMap(row=>s.moves.map((_,i)=>[...row,i]));return rows;}
function compare(a,b){for(let i=0;i<Math.min(a.length,b.length);i++)if(a[i]!==b[i])return a[i]-b[i];return a.length-b.length;}
export function analyzeRecurrence(raw){
 const input=validateRecurrence(raw),ss=input.arena.states,ns=ss.map(s=>s.name),by=new Map(ss.map((s,i)=>[s.name,i])),goals=new Set(input.goals),players=['controller','environment'];
 const owned=Object.fromEntries(players.map(p=>[p,ss.map((s,i)=>({s,i})).filter(({s})=>s.safe&&s.owner===p)]));
 const choices=Object.fromEntries(players.map(p=>[p,assignments(owned[p].map(x=>x.s))]));
 const policies=Object.fromEntries(players.map(p=>[p,choices[p].map(a=>new Map(owned[p].map(({i},j)=>[i,a[j]])))]));
 const failures=Object.fromEntries(players.map(p=>[p,policies[p].map(()=>ns.map(()=>null))]));
 for(let ci=0;ci<policies.controller.length;ci++)for(let ei=0;ei<policies.environment.length;ei++){
  const selection=new Map([...policies.controller[ci],...policies.environment[ei]]);
  for(let root=0;root<ss.length;root++){
   let n=root;const seen=new Map(),nodes=[],path=[],key=[];
   while(ss[n].safe&&!seen.has(n)){seen.set(n,nodes.length);nodes.push(n);const k=selection.get(n),m=ss[n].moves[k];path.push({from:ns[n],action:m.action,to:m.to});key.push(k);n=by.get(m.to);}
   let p,witness;
   if(!ss[n].safe){p='controller';witness={kind:'unsafe_path',path,cycle_start:null};}
   else{const start=seen.get(n),hit=nodes.slice(start).some(i=>goals.has(ns[i]));p=hit?'environment':'controller';witness={kind:hit?'safe_recurrent_lasso':'goal_avoiding_lasso',path,cycle_start:start};}
   const id=p==='controller'?ci:ei,old=failures[p][id][root];
   if(old===null||compare(key,old.key)<0)failures[p][id][root]={key,witness};
  }
 }
 const policy_atlases=Object.fromEntries(players.map(p=>[p,policies[p].map((policy,id)=>({id,policy:[...policy].map(([i,k])=>({state:ns[i],action:ss[i].moves[k].action})),outcomes:ns.map((start,i)=>({start,winning:failures[p][id][i]===null,failure:failures[p][id][i]?.witness??null}))}))]));
 const winning=ns.filter((n,i)=>policy_atlases.controller.some(r=>r.outcomes[i].winning)),losing=ns.filter(n=>!winning.includes(n));
 const states=ns.map((state,i)=>({state,winning:winning.includes(state),controller_policy_ids:policy_atlases.controller.filter(r=>r.outcomes[i].winning).map(r=>r.id),environment_policy_ids:policy_atlases.environment.filter(r=>r.outcomes[i].winning).map(r=>r.id)}));
 const uniform_policy_ids=Object.fromEntries(players.map(p=>[p,policy_atlases[p].filter(r=>ns.every((n,i)=>!(p==='controller'?winning:losing).includes(n)||r.outcomes[i].winning)).map(r=>r.id)]));
 for(const p of players)if(uniform_policy_ids[p].length===0)throw Error('no uniform positional strategy');
 for(const r of states)if(Boolean(r.environment_policy_ids.length)===r.winning)throw Error('strategy determinacy mismatch');
 let z=ss.reduce((m,s,i)=>m|(s.safe?1<<i:0),0);const outer=[],ordered=mask=>ns.filter((_,i)=>(mask&(1<<i))!==0);
 for(;;){let y=0;const inner=[];
  for(;;){let after=0;const checks=ss.map((s,i)=>{const tz=s.moves.map(m=>Boolean(z&(1<<by.get(m.to)))),ty=s.moves.map(m=>Boolean(y&(1<<by.get(m.to)))),op=s.owner==='controller'?xs=>xs.some(Boolean):xs=>xs.every(Boolean),reset=goals.has(s.name)&&op(tz),progress=op(ty),admitted=s.safe&&(reset||progress);if(admitted)after|=1<<i;return {state:s.name,operator:s.owner==='controller'?'exists':'all',safe:s.safe,goal:goals.has(s.name),target_in_outer:tz,target_in_inner:ty,reset,progress,admitted};});
   inner.push({index:inner.length,before:ordered(y),checks,after:ordered(after),added:ordered(after&~y)});if(y===after)break;y=after;
  }
  outer.push({index:outer.length,before:ordered(z),inner,after:ordered(y),removed:ordered(z&~y)});if(z===y)break;z=y;
 }
 if(JSON.stringify(ordered(z))!==JSON.stringify(winning))throw Error('policy/fixed-point disagreement');
 const proof_graphs=ns.map((start,root)=>{const player=winning.includes(start)?'controller':'environment',policy_id=uniform_policy_ids[player][0],policy=policies[player][policy_id],queue=[root],nodes=[start],edges=[];
  for(const i of queue){const s=ss[i];if(!s.safe)continue;for(let k=0;k<s.moves.length;k++){if(s.owner===player&&policy.get(i)!==k)continue;const m=s.moves[k],j=by.get(m.to);edges.push({from:s.name,action:m.action,to:m.to});if(!queue.includes(j)){queue.push(j);nodes.push(m.to);}}}
  return {start,player,policy_id,nodes,edges,unsafe:queue.filter(i=>!ss[i].safe).map(i=>ns[i])};
 });
 return {schema:'shieldlab-recurrence-v1',input,outer,winning,losing,policy_atlases,states,uniform_policy_ids,proof_graphs};
}
