import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {execFileSync} from 'node:child_process';
import {analyzeReachAvoid,validateReachAvoid,parseReachAvoidJSON} from '../docs/reachavoid-engine.js';

test('whole native reports agree with independent policy-based JavaScript',()=>{
 const source=`import json,sys,random,itertools
sys.path.insert(0,'tests')
from test_reachavoid import graph,CONTROLS
from shieldlab.reachavoid import analyze_reachavoid
cases=[c['input']for c in CONTROLS]
subs=[(0,),(1,),(0,1)]
for edges in itertools.product(subs,repeat=2):
 for owner in range(4):
  for status in itertools.product(range(3),repeat=2):cases.append(graph(2,edges,owner,status))
rng=random.Random(28119)
for k in range(120):
 n=4+k%3;cases.append(graph(n,[rng.sample(range(n),rng.randint(1,3))for _ in range(n)],rng.randrange(1<<n),[rng.randrange(3)for _ in range(n)]))
cases.append(graph(6,[(i,(i+1)%6,(i+2)%6)for i in range(6)],63,[1]*6))
print(json.dumps([analyze_reachavoid(c)for c in cases]))`;
 const reports=JSON.parse(execFileSync(process.env.PYTHON||'python',['-c',source],{maxBuffer:128*1024*1024}));
 let policies=0,outcomes=0,rounds=0;
 for(const expected of reports){const input=structuredClone(expected.input);const got=analyzeReachAvoid(input);assert.deepEqual(got,expected);assert.deepEqual(input,expected.input);policies+=got.policy_count;outcomes+=got.policy_atlas.reduce((n,a)=>n+a.outcomes.length,0);rounds+=got.rounds.length;}
 assert.equal(reports.length,457);console.log(JSON.stringify({reports:reports.length,policies,outcomes,rounds}));
});

test('strict duplicate/nonfinite/oversize JSON and schema rejection',()=>{
 const controls=JSON.parse(fs.readFileSync(new URL('../docs/reachavoid-controls.json',import.meta.url)));
 for(const c of controls)assert.deepEqual(analyzeReachAvoid(parseReachAvoidJSON(JSON.stringify(c.input))),analyzeReachAvoid(c.input));
 for(const raw of ['{"a":1,"a":2}','{"a":{"b":1,"b":2}}','[NaN]','1e999','01','true false','[1,]','{"a":1,}','"bad\nstring"','\u00a0{}',' '.repeat(65537)])assert.throws(()=>parseReachAvoidJSON(raw),raw.slice(0,40));
 for(const goals of [null,{},'done',['done','done'],['bad'],[true],['unknown']]){const c=structuredClone(controls[0].input);c.goals=goals;assert.throws(()=>validateReachAvoid(c));}
 const a=analyzeReachAvoid(controls[0].input);a.states[0].moves[0].to='changed';assert.equal(a.input.arena.states[0].moves[0].to,'choose');
 const request={arena:{states:[{name:'constructor',owner:'controller',safe:true,moves:[{action:'then',to:'toString'}]},{name:'toString',owner:'environment',safe:true,moves:[{action:'stay',to:'toString'}]}]},goals:['toString']};assert.equal(analyzeReachAvoid(request).states[0].rank,1);
});
