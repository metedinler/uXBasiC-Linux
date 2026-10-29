import { ux } from "./ux_runtime.js";

function ensureUxbRoot() {
  const root = globalThis.uxb || (globalThis.uxb = {});
  root.wasm = root.wasm || {};
  return root;
}

function makeCoreImports(overrides = {}) {
  const root = ensureUxbRoot();
  const write = value => {
    if (root.console && typeof root.console.print === "function") root.console.print(value);
    else if (ux && typeof ux.print === "function" && typeof document !== "undefined") ux.print(value);
    else console.log(value);
  };
  const newline = () => {
    if (root.console && typeof root.console.println === "function") root.console.println("");
    else if (ux && typeof ux.println === "function" && typeof document !== "undefined") ux.println();
    else console.log("");
  };
  let rngState = 0x6d2b79f5 | 0;
  const nextRandomI32 = () => {
    let x = rngState | 0;
    x ^= x << 13;
    x ^= x >>> 17;
    x ^= x << 5;
    rngState = x || (0x6d2b79f5 | 0);
    return rngState & 0x7fffffff;
  };
  const checkedI32 = (value, label) => {
    if (!Number.isFinite(value) || value < -2147483648 || value > 2147483647) {
      throw new Error(`${label} result is outside i32`);
    }
    return value | 0;
  };
  const hostCall4 = (id, a, b, c, d) => {
    switch (id | 0) {
      case 1: write(a | 0); return a | 0;
      case 1000: newline(); return 0;
      case 3: { const d = new Date(); return (d.getHours() * 3600 + d.getMinutes() * 60 + d.getSeconds()) | 0; } // S-624: tamsayi yolu = yerel gece yarisindan beri tam saniye
      case 4: return nextRandomI32();
      case 5: rngState = (a | 0) || (0x6d2b79f5 | 0); return a | 0;
      case 10:
        if ((a | 0) === -2147483648) throw new Error("ABS host call overflows i32");
        return Math.abs(a | 0) | 0;
      case 11:
        if ((a | 0) < 0) throw new Error("SQR host call requires non-negative input");
        return checkedI32(Math.sqrt(a | 0), "SQR");
      case 12: return checkedI32(Math.sin(a | 0), "SIN");
      case 13: return checkedI32(Math.cos(a | 0), "COS");
      case 14: return checkedI32(Math.tan(a | 0), "TAN");
      case 15: return checkedI32(Math.atan(a | 0), "ATAN");
      case 16:
        if ((a | 0) <= 0) throw new Error("LOG host call requires positive input");
        return checkedI32(Math.log(a | 0), "LOG");
      case 17: return checkedI32(Math.exp(a | 0), "EXP");
      default:
        if (typeof root.wasm.hostCall4 === "function") return root.wasm.hostCall4(id|0,a|0,b|0,c|0,d|0)|0;
        if (typeof globalThis.uxbHostCall4 === "function") return globalThis.uxbHostCall4(id|0,a|0,b|0,c|0,d|0)|0;
        throw new Error(`uXBasic WASM host import is not bound: id=${id}`);
    }
  };
  const defaults = { ux: {
    host_call4: hostCall4,
    print_i32: value => write(value | 0),
    print_f64: value => write(Number(value))
  }};
  return { ...defaults, ...overrides, ux: { ...defaults.ux, ...(overrides.ux || {}) } };
}

export async function loadUxWasm(path, imports = {}) {
  const merged = makeCoreImports(imports);
  let result;
  try {
    result = await WebAssembly.instantiateStreaming(fetch(path), merged);
  } catch (streamErr) {
    const response = await fetch(path);
    if (!response.ok) throw new Error(`WASM fetch failed: ${response.status} ${response.statusText}`);
    result = await WebAssembly.instantiate(await response.arrayBuffer(), merged);
  }
  const root = ensureUxbRoot();
  root.wasm.provider = "browser-webassembly/core-i32";
  root.wasm.instance = result.instance;
  root.wasm.exports = result.instance.exports;
  ux.wasm = result.instance.exports; // legacy compatibility
  return result.instance.exports;
}

export async function loadUxWasmFromManifest(manifestPath = "./wasm_manifest.json") {
  const response = await fetch(manifestPath);
  if (!response.ok) throw new Error(`WASM manifest fetch failed: ${response.status}`);
  const manifest = await response.json();
  const modulePath = manifest.module || manifest.wasm || "./program.wasm";
  return loadUxWasm(modulePath);
}
