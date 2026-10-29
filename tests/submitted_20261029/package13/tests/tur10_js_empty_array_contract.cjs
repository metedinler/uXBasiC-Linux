const assert = require('node:assert/strict');
require(require('node:path').resolve(process.argv[2] || '../../runtime/js/common/ux_runtime_core.js'));
const ux = globalThis.uxb.data;
let passed = 0;
function check(name, fn) { fn(); passed++; console.log(`PASS ${name}`); }
const a = ux.arrayNew(0, 0, 0);
check('empty lower=0 upper=-1', () => { assert.equal(ux.arrayLBound(a),0); assert.equal(ux.arrayUBound(a),-1); });
check('empty read refused', () => assert.throws(()=>ux.arrayLoad(a,0), /array index out of bounds/));
check('empty write refused', () => assert.throws(()=>ux.arrayStore(a,0,5), /array index out of bounds/));
check('redim from empty', () => { ux.arrayResize(a,6,0,0,false); assert.equal(ux.arrayUBound(a),5); });
check('read/write after redim', () => { ux.arrayStore(a,5,42); assert.equal(ux.arrayLoad(a,5),42); });
check('preserve when changing lower bound', () => {ux.arrayResize(a,6,0,2,true); assert.equal(ux.arrayLBound(a),2); assert.equal(ux.arrayUBound(a),7); assert.equal(ux.arrayLoad(a,5),42);});
check('forwarded alias identity survives redim', ()=> {const alias=a; ux.arrayResize(a,3,0,2,true); assert.equal(alias,a); assert.equal(ux.arrayLBound(alias),2); assert.equal(ux.arrayUBound(alias),4); });
check('rejected out-of-range after shrink', () => assert.throws(()=>ux.arrayLoad(a,5), /array index out of bounds/));
console.log(JSON.stringify({passed,total:8,kind:'actual JS runtime, not compiler E2E'}));
