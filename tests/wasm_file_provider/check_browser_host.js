// Exercise the actual emitted module/runtime with browser-like capabilities.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const [runtimePath, wasmPath, entry = 'MAIN'] = process.argv.slice(2);
if (!runtimePath || !wasmPath) throw new Error('usage: node check_browser_host.js runtime.js module.wasm [entry]');
const scope = vm.createContext({console, WebAssembly, TextEncoder, TextDecoder});
vm.runInContext(fs.readFileSync(runtimePath, 'utf8'), scope, {filename:runtimePath});
WebAssembly.instantiate(fs.readFileSync(wasmPath), scope.uxbWasmImports).then(({instance}) => {
  scope.uxbWasmInstance = instance;
  assert.throws(() => instance.exports[entry](), /UXB_WASM_FILE_PROVIDER_MISSING/);
  assert.equal(fs.existsSync('browser_no_provider.txt'), false);
  console.log('PASS actual WASM browser host: missing file capability is explicit and creates no file');
}).catch(error => { console.error(error); process.exitCode = 1; });
