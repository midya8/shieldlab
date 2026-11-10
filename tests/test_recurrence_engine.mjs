import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {execFileSync} from 'node:child_process';
import {analyzeRecurrence,validateRecurrence,parseRecurrenceJSON} from '../docs/recurrence-engine.js';
test('complete independent strategy-pair JS agrees with native nested solver and separate checker',()=>{
 const script=`import json,sys,random,itertools
sys.path.insert(0,'tests')
from test_recurrence import graph
from shieldlab.recurrence import analyze_recurrence
from shieldlab.recurrence_verify import verify_recurrence
cases=[c['input']for c in json.load(open('docs/recurrence-controls.json'))]
for edges in itertools.product([(0,),(1,),(0,1)],repeat=2):
 for owner in range(4):
  for status in itertools.product(range(3),repeat=2):cases.append(graph(2,edges,owner,status))
rng=random.Random(231862)
for k in range(160):
 n=4+k%3;cases.append(graph(n,[rng.sample(range(n),rng.randint(1,3))for _ in range(n)],rng.randrange(1<<n),[rng.randrange(3)for _ in range(n)]))
for owner in [0,63]:cases.append(graph(6,[(i,(i+1)%6,(i+2)%6)for i in range(6)],owner,[2,1,1,1,1,1]))
reports=[analyze_recurrence(c)for c in cases]
assert all(verify_recurrence(r)for r in reports)
print(json.dumps(reports))`;
 const reports=JSON.parse(execFileSync(process.env.PYTHON||'python',['-c',script],{maxBuffer:128*1024*1024}));
 const counts={reports:reports.length,outer:0,inner:0,obligations:0,policies:0,outcomes:0,proof_edges:0};
 for(const expected of reports){const input=structuredClone(expected.input),got=analyzeRecurrence(input);assert.deepEqual(got,expected);assert.deepEqual(input,expected.input);counts.outer+=got.outer.length;for(const o of got.outer){counts.inner+=o.inner.length;for(const r of o.inner)counts.obligations+=r.checks.length;}for(const atlas of Object.values(got.policy_atlases)){counts.policies+=atlas.length;for(const row of atlas)counts.outcomes+=row.outcomes.length;}counts.proof_edges+=got.proof_graphs.reduce((n,g)=>n+g.edges.length,0);}
 assert.equal(reports.length,498);console.log(JSON.stringify(counts));
});
test('strict JSON, schema, target nonterminal and dangerous property names',()=>{
 const controls=JSON.parse(fs.readFileSync(new URL('../docs/recurrence-controls.json',import.meta.url)));
 for(const c of controls)assert.deepEqual(analyzeRecurrence(parseRecurrenceJSON(JSON.stringify(c.input))).winning,c.expected_winning);
 for(const raw of ['{"arena":{},"arena":{},"goals":[]}','{"x":{"a":1,"a":2}}','1e999','[NaN]','01','true false','[1,]','{"a":1,}','"bad\nstring"','\u00a0{}',' '.repeat(65537)])assert.throws(()=>parseRecurrenceJSON(raw));
 for(const goals of [null,{},'ack',['ack','ack'],['unknown'],[true]]){const c=structuredClone(controls[0].input);c.goals=goals;assert.throws(()=>validateRecurrence(c));}
 const c=structuredClone(controls[0].input);c.arena.states[0].moves=[];assert.throws(()=>validateRecurrence(c));
 const d={arena:{states:[{name:'constructor',owner:'controller',safe:true,moves:[{action:'then',to:'toString'}]},{name:'toString',owner:'environment',safe:true,moves:[{action:'stay',to:'constructor'}]}]},goals:['toString']};assert.deepEqual(analyzeRecurrence(d).winning,['constructor','toString']);
 const a=analyzeRecurrence(controls[0].input);a.proof_graphs[0].edges[0].to='changed';assert.equal(a.input.arena.states[0].moves[0].to,'ack');
});
