import {validate} from './engine.js';
export function validateReachAvoid(data){
 if(data===null||typeof data!=='object'||Array.isArray(data)||Object.keys(data).sort().join('|')!=='arena|goals')throw Error('request needs exactly arena and goals');
 const arena=validate(data.arena),names=arena.states.map(s=>s.name);
 if(!Array.isArray(data.goals)||data.goals.some(n=>typeof n!=='string'||!names.includes(n))||new Set(data.goals).size!==data.goals.length)throw Error('goals must be unique declared names');
 if(arena.states.some(s=>!s.safe&&data.goals.includes(s.name)))throw Error('goals must be safe; unsafe/goal overlap rejected');
 return {arena,goals:names.filter(n=>data.goals.includes(n))};
}

export function parseReachAvoidJSON(raw){
 if(new TextEncoder().encode(raw).length>65536)throw Error('input exceeds65536 bytes');
 let p=0;const ws=()=>{while(/[ \t\r\n]/.test(raw[p]??'')&&p<raw.length)p++;};
 function string(){const start=p++;while(p<raw.length){if(raw[p]==='\\'){p+=2;continue;}if(raw[p++]==='"')return JSON.parse(raw.slice(start,p));}throw Error('unterminated string');}
 function value(){ws();const c=raw[p];
  if(c==='"')return string();
  if(c==='{'){p++;const keys=new Set(),out=Object.create(null);ws();if(raw[p]==='}'){p++;return out;}while(true){ws();if(raw[p]!=='"')throw Error('object key must be string');const k=string();if(keys.has(k))throw Error('duplicate JSON key');keys.add(k);ws();if(raw[p++]!==':')throw Error('missing colon');out[k]=value();ws();const sep=raw[p++];if(sep==='}')return out;if(sep!==',')throw Error('missing comma');}}
  if(c==='['){p++;const out=[];ws();if(raw[p]===']'){p++;return out;}while(true){out.push(value());ws();const sep=raw[p++];if(sep===']')return out;if(sep!==',')throw Error('missing comma');}}
  for(const [token,v]of [['true',true],['false',false],['null',null]])if(raw.startsWith(token,p)){p+=token.length;return v;}
  const number=raw.slice(p).match(/^-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?/);if(!number)throw Error('invalid JSON value');p+=number[0].length;const n=Number(number[0]);if(!Number.isFinite(n))throw Error('nonfinite JSON number');return n;
 }
 const result=value();ws();if(p!==raw.length)throw Error('trailing JSON content');return result;
}

function* assignments(states,i=0,choices=[]){
 if(i===states.length){yield choices;return;}
 for(let j=0;j<states[i].moves.length;j++)yield*assignments(states,i+1,[...choices,j]);
}
function outcome(by,goals,policy,start){
 const stack=[{n:start,nodes:[],path:[]}];let longest=null;
 while(stack.length){const{n,nodes,path}=stack.pop(),s=by.get(n);
  if(goals.has(n)){if(longest===null||path.length>longest.worst_steps)longest={start,winning:true,worst_steps:path.length,witness:{kind:'longest_goal_path',path,cycle_start:null}};continue;}
  if(!s.safe||nodes.includes(n))return {start,winning:false,worst_steps:null,witness:{kind:!s.safe?'unsafe_path':'goal_avoiding_lasso',path,cycle_start:nodes.includes(n)?nodes.indexOf(n):null}};
  const moves=s.owner==='controller'?[s.moves[policy.get(n)]]:s.moves;
  for(let i=moves.length-1;i>=0;i--){const m=moves[i];stack.push({n:m.to,nodes:[...nodes,n],path:[...path,{from:n,...m}]});}
 }
 return longest;
}
function safePolicy(by,goals,policy,start){
 const seen=new Set([start]),queue=[start];
 for(const n of queue){const s=by.get(n);if(!s.safe)return false;if(goals.has(n))continue;const moves=s.owner==='controller'?[s.moves[policy.get(n)]]:s.moves;for(const m of moves)if(!seen.has(m.to)){seen.add(m.to);queue.push(m.to);}}
 return true;
}

export function analyzeReachAvoid(raw){
 const input=validateReachAvoid(raw),states=input.arena.states,names=states.map(s=>s.name),by=new Map(states.map(s=>[s.name,s])),goals=new Set(input.goals),order=set=>names.filter(n=>set.has(n));
 const controlled=states.filter(s=>s.safe&&!goals.has(s.name)&&s.owner==='controller'),atlas=[],best=new Map(),safe=new Set();
 for(const choices of assignments(controlled)){const policy=new Map(controlled.map((s,i)=>[s.name,choices[i]]));const outcomes=names.map(n=>{const out=outcome(by,goals,policy,n);if(out.winning)best.set(n,Math.min(best.get(n)??Infinity,out.worst_steps));if(safePolicy(by,goals,policy,n))safe.add(n);return out;});atlas.push({id:atlas.length,policy:controlled.map((s,i)=>({state:s.name,action:s.moves[choices[i]].action})),outcomes});}
 const winning=new Set(best.keys()),rounds=[];
 for(let index=0;;index++){const before=new Set(names.filter(n=>best.has(n)&&best.get(n)<=index)),after=new Set(names.filter(n=>best.has(n)&&best.get(n)<=index+1));const checks=states.map(s=>{const ts=s.moves.map(m=>before.has(m.to)),qualified=s.owner==='controller'?ts.some(Boolean):ts.every(Boolean),admitted=goals.has(s.name)||(s.safe&&qualified);if(admitted!==after.has(s.name))throw Error('policy evidence disagrees with local obligation');return {state:s.name,operator:s.owner==='controller'?'exists':'all',safe:s.safe,goal:goals.has(s.name),target_in_before:ts,qualified,admitted};});const added=names.filter(n=>after.has(n)&&!before.has(n));rounds.push({index,before:order(before),checks,after:order(after),added});if(added.length===0)break;}
 const records=states.map(s=>{const n=s.name,active=s.safe&&!goals.has(n),moves=s.moves.map(m=>({...m,target_winning:best.has(m.to),target_rank:best.get(m.to)??null,optimal_controller_move:active&&s.owner==='controller'&&best.has(n)&&best.has(m.to)&&best.get(m.to)+1===best.get(n)}));return {name:n,owner:s.owner,safe:s.safe,goal:goals.has(n),winning:best.has(n),rank:best.get(n)??null,moves,controller_choice:moves.find(m=>m.optimal_controller_move)?.action??null,environment_choice:moves.find(m=>active&&s.owner==='environment'&&!best.has(n)&&!m.target_winning)?.action??null};});
 const rb=new Map(records.map(r=>[r.name,r])),proof_graphs=records.map(root=>{const nodes=[root.name],edges=[];for(const n of nodes){const s=rb.get(n);if(s.goal||!s.safe)continue;const owner=root.winning?'controller':'environment';for(const m of s.moves){if(s.owner===owner&&m.action!==s[owner+'_choice'])continue;edges.push({from:n,action:m.action,to:m.to});if(!nodes.includes(m.to))nodes.push(m.to);}}return {start:root.name,kind:root.winning?'ranked_goal_strategy':'goal_avoiding_counterstrategy',nodes,edges,goals:nodes.filter(n=>goals.has(n)),unsafe:nodes.filter(n=>!by.get(n).safe),rank_bound:root.rank};});
 const policy_summaries=names.map((state,i)=>({state,winning_policy_ids:atlas.filter(a=>a.outcomes[i].winning).map(a=>a.id),optimal_policy_ids:atlas.filter(a=>a.outcomes[i].winning&&a.outcomes[i].worst_steps===best.get(state)).map(a=>a.id)}));
 return {schema:'shieldlab-reachavoid-v1',input,rounds,winning:order(winning),losing:names.filter(n=>!winning.has(n)),safe_until_goal:order(safe),safe_but_cannot_force_goal:names.filter(n=>safe.has(n)&&!winning.has(n)),states:records,proof_graphs,policy_count:atlas.length,policy_atlas:atlas,policy_summaries,uniform_optimal_policy_ids:atlas.filter(a=>names.every((n,i)=>!best.has(n)||(a.outcomes[i].winning&&a.outcomes[i].worst_steps===best.get(n)))).map(a=>a.id),limits:LIMITS.slice()};
}

const LIMITS=["Goal is terminal success on first hit; outgoing goal moves are ignored, not an obligation to remain safe afterward.", "All goals must be safe. Unsafe roots fail immediately. Empty goals make every root lose reach-avoid.", "A finite total turn-based perfect-information adversarial arena; no fairness assumption, probabilities or real-system guarantee.", "A move to a winning successor may still allow endless stalling under repeated permissive choices. Only the displayed optimal rank-decreasing controller choices enforce the stated bound.", "Policy counts describe complete deterministic positional assignments on safe non-goal controller states, including unreachable states; not distinct behaviors or all history-dependent strategies.", "One to six states and one to three moves per state; exhaustive policy evidence is deliberately bounded, not a scalable solver or new algorithm."];
