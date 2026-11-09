import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import {execFileSync} from 'node:child_process';import {analyze,validate} from '../docs/engine.js';
const py=`import json,itertools,random
from shieldlab import analyze
from pathlib import Path
def game(n,edges,owners,safe):
 return {'states':[{'name':'s'+str(i),'owner':'controller' if owners>>i&1 else 'environment','safe':bool(safe>>i&1),'moves':[{'action':'a'+str(j),'to':'s'+str(t)} for j,t in enumerate(edges[i])]} for i in range(n)]}
xs=[c['input'] for c in json.loads(Path('docs/controls.json').read_text())]
for edges in itertools.product([[0],[1],[0,1]],repeat=2):
 for owner in range(4):
  for safe in range(4):xs.append(game(2,edges,owner,safe))
for edges in itertools.product([[i for i in range(3) if b>>i&1] for b in range(1,8)],repeat=3):xs.append(game(3,edges,3,6))
rng=random.Random(404)
for _ in range(150):
 n=rng.randint(1,6);xs.append(game(n,[[rng.randrange(n) for j in range(rng.randint(1,3))] for i in range(n)],rng.randrange(1<<n),rng.randrange(1<<n)))
print(json.dumps([analyze(x) for x in xs]))`;
test('independent JavaScript equals complete native safety certificates',()=>{const reports=JSON.parse(execFileSync(process.env.PYTHON||'python',['-c',py],{maxBuffer:64*1024*1024}));let rounds=0,obligations=0,moves=0,proof_edges=0;for(const r of reports){const x=structuredClone(r.input),before=structuredClone(x);assert.deepEqual(analyze(x),r);assert.deepEqual(x,before);rounds+=r.rounds.length;obligations+=r.rounds.reduce((n,r)=>n+r.checks.length,0);moves+=r.states.reduce((n,s)=>n+s.moves.length,0);proof_edges+=r.proof_graphs.reduce((n,p)=>n+p.edges.length,0);}assert.equal(reports.length,643);console.log(JSON.stringify({reports:reports.length,rounds,obligations,moves,proof_edges}));});
test('strict schema, immutability and dead-end rejection',()=>{for(const x of [{},{states:[]},{states:[{}]},{states:[{name:'x',owner:'controller',safe:true,moves:[]}]}])assert.throws(()=>validate(x));const c=JSON.parse(fs.readFileSync(new URL('../docs/controls.json',import.meta.url)))[0].input;for(const fn of [x=>x.states[0].safe=1,x=>x.states[0].owner='random',x=>x.states[0].moves[0].to='missing',x=>x.states[0].moves.push(x.states[0].moves[0]),x=>x.extra=true]){const x=structuredClone(c);fn(x);assert.throws(()=>validate(x));}});
