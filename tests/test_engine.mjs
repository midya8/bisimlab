import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import {execFileSync} from 'node:child_process';import {analyze} from '../docs/engine.js';
const controls=JSON.parse(fs.readFileSync(new URL('../docs/controls.json',import.meta.url)));
test('independent JavaScript matches complete Python reports',()=>{
 let seed=1809;const rng=()=>{seed=(1664525*seed+1013904223)>>>0;return seed/2**32;};
 const systems=controls.map(c=>c.system);
 for(let m=0;m<512;m++){const states=['p','q','r'],edges=[];let i=0;for(const p of states)for(const q of states){if(m>>i&1)edges.push([p,'a',q]);i++;}systems.push({states,actions:['a'],edges});}
 for(let j=0;j<75;j++){const states=Array.from({length:1+Math.floor(rng()*6)},(_,i)=>'s'+i),actions=['a','b','c'].slice(0,Math.floor(rng()*4)),edges=[];for(const p of states)for(const a of actions)for(const q of states)if(rng()<.2&&edges.length<18)edges.push([p,a,q]);systems.push({states,actions,edges});}
 const expected=JSON.parse(execFileSync(process.env.PYTHON||'python',['-c','import sys,json;from bisimlab import analyze;print(json.dumps([analyze(d) for d in json.load(sys.stdin)]))'],{input:JSON.stringify(systems),maxBuffer:128*1024*1024}));
 systems.forEach((s,i)=>assert.deepEqual(analyze(s),expected[i],`system ${i}`));console.log(JSON.stringify({systems:systems.length,pairs:expected.reduce((a,r)=>a+r.pairs.length,0),rounds:expected.reduce((a,r)=>a+r.rounds.length,0),nodes:expected.reduce((a,r)=>a+r.formulas.length,0)}));
});
test('JavaScript strict validation and input immutability',()=>{for(const bad of [null,{},[],{states:[],actions:[],edges:[]},{...controls[0].system,extra:1},{states:['p'],actions:['a'],edges:[['p','a','p'],['p','a','p']]}])assert.throws(()=>analyze(bad));const d=structuredClone(controls[0].system),before=structuredClone(d);analyze(d);assert.deepEqual(d,before);});
