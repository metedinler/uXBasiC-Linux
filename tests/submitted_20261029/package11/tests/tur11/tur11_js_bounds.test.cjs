'use strict';
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const runtime = fs.readFileSync(process.argv[2], 'utf8');
const c = { console, process: { stdout: { write() {} } } };
vm.createContext(c);
vm.runInContext(runtime, c, { filename: process.argv[2] });
const ux = c.uxb.data;
let passed = 0;
function check(name, f) { f(); passed++; console.log('PASS',name); }
function rejected(f, code) {
  assert.throws(f, e => e.code === code);
}
check('zero element array bounds 0/-1',()=>{const a=ux.arrayNew(0,0,0);assert.equal(ux.arrayLBound(a),0);assert.equal(ux.arrayUBound(a),-1);});
check('empty array read rejects',()=>{const a=ux.arrayNew(0,0,0);rejected(()=>ux.arrayLoad(a,0),'UXB_ARRAY_INDEX');});
check('null reference read rejects, never returns zero',()=>rejected(()=>ux.arrayLoad(null,0),'UXB_ARRAY_TARGET_MISSING'));
check('zero-based valid read and write',()=>{const a=ux.arrayNew(2,0,0);ux.arrayStore(a,1,71);assert.equal(ux.arrayLoad(a,1),71);});
check('2^32 read cannot alias index zero',()=>{const a=ux.arrayNew(1,77,0);rejected(()=>ux.arrayLoad(a,4294967296),'UXB_ARRAY_INDEX');});
check('minus 2^32 read cannot alias index zero',()=>{const a=ux.arrayNew(1,77,0);rejected(()=>ux.arrayLoad(a,-4294967296),'UXB_ARRAY_INDEX');});
check('2^32 store cannot change element zero',()=>{const a=ux.arrayNew(1,77,0);rejected(()=>ux.arrayStore(a,4294967296,92),'UXB_ARRAY_INDEX');assert.equal(a[0],77);});
check('fractional, NaN, infinity reject',()=>{const a=ux.arrayNew(1,77,0);for (const i of [0.75,NaN,Infinity,-Infinity])rejected(()=>ux.arrayLoad(a,i),'UXB_ARRAY_INDEX');});
check('unsafe large number is rejected',()=>{const a=ux.arrayNew(1,77,0);rejected(()=>ux.arrayLoad(a,9007199254740993),'UXB_ARRAY_INDEX');});
check('valid negative lower bound',()=>{const a=ux.arrayNew(3,0,-2);ux.arrayStore(a,-1,33);assert.equal(ux.arrayLoad(a,-1),33);});
check('index outside negative lower bound rejects',()=>{const a=ux.arrayNew(3,0,-2);rejected(()=>ux.arrayLoad(a,1),'UXB_ARRAY_INDEX');});
check('valid index above signed i32 range',()=>{const a=ux.arrayNew(2,0,4294967296);ux.arrayStore(a,4294967297,44);assert.equal(ux.arrayLoad(a,4294967297),44);});
check('REDIM preserve after empty',()=>{const a=ux.arrayNew(0,0,0);ux.arrayResize(a,4,0,2,true);ux.arrayStore(a,3,81);ux.arrayResize(a,3,0,3,true);assert.equal(ux.arrayLoad(a,3),81);assert.equal(ux.arrayUBound(a),5);});
check('TYPE record indexing detects wraparound',()=>{const a=ux.arrayNew(1,0,0);rejected(()=>ux.arrayFieldRecord(a,4294967296),'UXB_ARRAY_INDEX');});
console.log(JSON.stringify({total:passed,result:'PASS'}));
