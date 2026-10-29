// Extracted verbatim from wasm_runtime_bridge.fbs case 80..85, current source snapshot.
const assert = require('node:assert/strict');
const arrays=new Map();let nextHandle=1;
function host(id,a,b,c,d) {switch(id|0){
    case 80: { const h=nextHandle++; const n=Math.max(0,a|0); arrays.set(h,{lower:c|0,data:new Array(n).fill(b|0)}); return h|0; }
    case 81: { const r=arrays.get(a|0); if(!r) throw new Error('UXB_WASM_ARRAY_MISSING:'+a); const i=(b|0)-(r.lower|0); if(i<0||i>=r.data.length) throw new Error('array index out of bounds'); return Number(r.data[i]||0)|0; }
    case 82: { const r=arrays.get(a|0); if(!r) throw new Error('UXB_WASM_ARRAY_MISSING:'+a); const i=(b|0)-(r.lower|0); if(i<0||i>=r.data.length) throw new Error('array index out of bounds'); r.data[i]=c|0; return c|0; }
    case 83: { const r=arrays.get(a|0); if(!r) throw new Error('UXB_WASM_ARRAY_MISSING:'+a); return r.lower|0; }
    case 84: { const r=arrays.get(a|0); if(!r) throw new Error('UXB_WASM_ARRAY_MISSING:'+a); return ((r.lower|0)+r.data.length-1)|0; }
    case 85: { const r=arrays.get(a|0); if(!r) throw new Error('UXB_WASM_ARRAY_MISSING:'+a); const lo=b|0, hi=c|0, n=hi-lo+1; if(n<1||n>268435455) throw new Error('array invalid bounds or byte size overflow'); const data=new Array(n).fill(0); if(d){const start=Math.max(lo,r.lower),end=Math.min(hi,r.lower+r.data.length-1); for(let i=start;i<=end;i++) data[i-lo]=r.data[i-r.lower];} r.data=data; r.lower=lo; return a|0; }
}}
let p=0; const check=(name,fn)=>{fn(); console.log(`PASS ${name}`);p++};
const id=host(80,0,0,0,0);
check('empty bounds',()=>{assert.equal(host(83,id,0,0,0),0);assert.equal(host(84,id,0,0,0),-1)});
check('empty read OOB',()=>assert.throws(()=>host(81,id,0,0,0),/array index out of bounds/));
check('empty write OOB',()=>assert.throws(()=>host(82,id,0,7,0),/array index out of bounds/));
check('redim allocates',()=>{host(85,id,0,5,0);assert.equal(host(84,id,0,0,0),5)});
check('read/write',()=>{host(82,id,5,66,0);assert.equal(host(81,id,5,0,0),66)});
check('redim preserve',()=>{host(85,id,2,7,1);assert.equal(host(81,id,5,0,0),66);assert.equal(host(83,id,0,0,0),2);assert.equal(host(84,id,0,0,0),7)});
console.log(JSON.stringify({passed:p,total:6,scope:'extracted WASM host bridge array handlers, not WAT execution'}));
