/*
 * uXBasic JavaScript host contract v1.
 * Source of truth for generated JS, browser providers and QuickJS providers.
 *
 * Public global: globalThis.uxb
 * Temporary compatibility alias: globalThis.ux -> globalThis.uxb.compat
 */
(function bootstrapUxBasicRuntime(globalObject) {
  "use strict";

  const CONTRACT_VERSION = 1;
  const existing = globalObject.uxb;
  if (existing && existing.contractVersion === CONTRACT_VERSION && existing.compat) {
    if (!globalObject.ux) globalObject.ux = existing.compat;
    return;
  }

  const state = {
    out: [],
    pending: "",
    printColumn: 0,
    channel: "screen",
    cursor: { row: 1, col: 1 },
    colorState: [],
    seed: 1,
    canvas: null,
    ctx: null,
    sink: null,
  };

  const fail = (code, message) => {
    const error = new Error(String(message || code));
    error.code = String(code);
    throw error;
  };

  // S-142b: the language's floating-point text rule, parameterized by the
  // declared precision. F64 uses 16 significant digits; F32 uses 7 after
  // Math.fround. This keeps JS PRINT/STR aligned with the other engines.
  const formatSignificantNumber = (value, digits) => {
    if (typeof value !== "number") return String(value);
    if (value === 0) return "0";
    if (Number.isNaN(value)) return "nan";
    if (!Number.isFinite(value)) return value < 0 ? "-inf" : "inf";
    if (digits >= 16 && Number.isSafeInteger(value)) return String(value);
    const scientific = value.toExponential(digits - 1);
    const parts = scientific.split("e");
    const exponent = Number(parts[1]);
    if (exponent < -4 || exponent >= digits) {
      const mantissa = parts[0].indexOf(".") >= 0 ? parts[0].replace(/\.?0+$/, "") : parts[0];
      const expDigits = String(Math.abs(exponent));
      return mantissa + "e" + (exponent < 0 ? "-" : "+") + (expDigits.length < 2 ? "0" + expDigits : expDigits);
    }
    const fixed = value.toFixed(Math.max(0, digits - 1 - exponent));
    return fixed.indexOf(".") >= 0 ? fixed.replace(/\.?0+$/, "") : fixed;
  };

  const formatNumber = (value) => formatSignificantNumber(value, 16);
  const formatF32 = (value) => formatSignificantNumber(Math.fround(Number(value)), 7);

  const uxb = {
    contractVersion: CONTRACT_VERSION,
    autoRun: true,
    provider: Object.freeze({ name: "unbound", version: "0", capabilities: [] }),
    exports: Object.create(null),
    system: {},
    file: {},
    net: {},
    storage: {},
    audio: {},
    input: {},
    ai: {},
    wasm: {},
  };

  const advanceCursor = text => {
    for (const ch of text) {
      if (ch === "\n") { state.cursor.row++; state.printColumn = 0; }
      else if (ch === "\r") state.printColumn = 0;
      else if (ch === "\t") state.printColumn += 8 - state.printColumn % 8;
      else if (ch === "\b") state.printColumn = Math.max(0, state.printColumn - 1);
      else if (ch.codePointAt(0) >= 32 && ch !== "\x7f") state.printColumn++;
    }
    state.cursor.col = state.printColumn + 1;
  };

  uxb.console = {
    setSink(sink) {
      if (!sink || (typeof sink.write !== "function" && typeof sink.writeLine !== "function")) {
        return fail("UXB_BAD_CONSOLE_SINK", "console sink must provide write or writeLine");
      }
      state.sink = sink;
      return 1;
    },
    print(...args) {
      const text = args.map(value => formatNumber(value)).join(" ");
      state.pending += text;
      advanceCursor(text);
      if (state.sink && typeof state.sink.write === "function") state.sink.write(text);
      else if (!state.sink && typeof process !== "undefined" && process.stdout) process.stdout.write(text);
      return text;
    },
    println(...args) {
      const text = args.map(value => formatNumber(value)).join(" ");
      const line = state.pending + text;
      state.pending = "";
      advanceCursor(text + "\n");
      state.out.push(line);
      if (state.sink && typeof state.sink.write === "function") {
        state.sink.write(text + "\n");
      } else if (!state.sink && typeof process !== "undefined" && process.stdout) {
        process.stdout.write(text + "\n");
      } else if (state.sink && typeof state.sink.writeLine === "function") {
        state.sink.writeLine(line);
      } else if (typeof globalObject.console !== "undefined" && typeof globalObject.console.log === "function") {
        globalObject.console.log(line);
      }
      return line;
    },
    separator(kind) {
      return this.print(kind === "comma" ? " ".repeat(14 - state.printColumn % 14) : " ");
    },
    formatF32,
    clear() {
      state.out.length = 0;
      state.pending = "";
      state.printColumn = 0;
      state.cursor = { row: 1, col: 1 };
      if (state.sink && typeof state.sink.clear === "function") state.sink.clear();
      else if (typeof process !== "undefined" && process.stdout?.isTTY) process.stdout.write("\x1b[2J\x1b[H");
      return 0;
    },
    lines() {
      return state.out.slice();
    },
  };

  uxb.time = {
    now: () => Date.now(),
    // S-624: TIMER = yerel gece yarisindan beri gecen kesirli saniye (tum motorlarda ayni tanim, src/common/uxb_clock.fbs).
    timer: () => { const d = new Date(); return d.getHours() * 3600 + d.getMinutes() * 60 + d.getSeconds() + d.getMilliseconds() / 1000; },
  };

  uxb.random = {
    seed(value = Date.now()) {
      state.seed = (Number(value) || 1) >>> 0;
      return state.seed;
    },
    u32() {
      state.seed = (Math.imul(1664525, state.seed) + 1013904223) >>> 0;
      return state.seed;
    },
    next() {
      return uxb.random.u32() / 4294967296;
    },
  };

  uxb.lang = {
    typeOf(value) {
      if (Array.isArray(value)) return "ARRAY";
      if (value === null || value === undefined) return "VOID";
      if (typeof value === "bigint") return "BIGINT";
      if (typeof value === "number") return "NUMBER";
      if (typeof value === "string") return "STRING";
      if (typeof value === "boolean") return "BOOLEAN";
      if (typeof value === "function") return "FUNCTION";
      return String(typeof value).toUpperCase();
    },
    sizeOf(name) {
      const key = String(name || "").toUpperCase();
      const sizes = {
        I8: 1, U8: 1, BYTE: 1, BOOLEAN: 1,
        I16: 2, U16: 2,
        I32: 4, U32: 4, F32: 4,
        I64: 8, U64: 8, F64: 8, PTR: 8, STRPTR: 8, OBJECT: 8,
        ANY: 16, VARIANT: 16, BIGINT: 16, BIGF: 32, BIGD: 32, BALL: 1,
      };
      if (!(key in sizes)) return fail("UXB_SIZEOF_LAYOUT_MISSING", `SIZEOF layout missing: ${key}`);
      return sizes[key];
    },
    offsetOf() {
      return fail("UXB_OFFSETOF_METADATA_REQUIRED", "OFFSETOF requires emitted layout metadata");
    },
    pointerOf() {
      return fail("UXB_POINTER_UNAVAILABLE", "pointer values are not available on the JavaScript target");
    },
    builtin(name, args = []) {
      const op = String(name || "").toUpperCase();
      const a = Array.isArray(args) ? args : [];
      switch (op) {
        case "ABS": return Math.abs(Number(a[0] || 0));
        case "SQR":
        case "SQRT": return Math.sqrt(Number(a[0] || 0));
        case "SIN": return Math.sin(Number(a[0] || 0));
        case "COS": return Math.cos(Number(a[0] || 0));
        case "TAN": return Math.tan(Number(a[0] || 0));
        case "ATN": return Math.atan(Number(a[0] || 0));
        case "LOG": return Math.log(Number(a[0] || 0));
        case "EXP": return Math.exp(Number(a[0] || 0));
        case "FIX": return Math.trunc(Number(a[0] || 0));
        case "INT": return Math.floor(Number(a[0] || 0));
        case "CINT":
        case "CLNG": {
          const value = Number(a[0] || 0);
          const lower = Math.floor(value);
          const fraction = value - lower;
          return fraction < 0.5 ? lower : fraction > 0.5 ? lower + 1 : lower % 2 === 0 ? lower : lower + 1;
        }
        case "CSNG":
        case "CDBL":
        case "VAL": return Number(a[0] || 0);
        case "SGN": return Math.sign(Number(a[0] || 0));
        case "RND": return uxb.random.next();
        case "TIMER": return uxb.time.timer();
        case "CSRLIN": return state.cursor.row;
        case "POS": return state.cursor.col;
        case "ASC": return String(a[0] || "").charCodeAt(0) || 0;
        case "CHR": return String.fromCharCode(Number(a[0] || 0));
        case "STR": return formatNumber(a[0]);
        case "LEN": return String(a[0] ?? "").length;
        // S-107: FOR EACH over a STRING walks Unicode CODE POINTS. JS strings are UTF-16, so a code
        // point outside the BMP is a surrogate PAIR (2 code units); CPLEN(s, pos) is the width (in
        // code units, matching LEN/MID's own unit) of the code point starting at 0-based unit pos.
        case "CPLEN": {
          const cpSource = String(a[0] ?? "");
          const cpPos = Number(a[1] || 0);
          if (cpPos < 0 || cpPos >= cpSource.length) return 1;
          const lead = cpSource.charCodeAt(cpPos);
          if (lead >= 0xd800 && lead <= 0xdbff && cpPos + 1 < cpSource.length) {
            const trail = cpSource.charCodeAt(cpPos + 1);
            if (trail >= 0xdc00 && trail <= 0xdfff) return 2;
          }
          return 1;
        }
        case "LEFT": return String(a[0] ?? "").substring(0, Number(a[1] || 0));
        case "RIGHT": {
          const source = String(a[0] ?? "");
          return source.substring(Math.max(0, source.length - Number(a[1] || 0)));
        }
        case "MID": {
          const source = String(a[0] ?? "");
          const start = Math.max(0, Number(a[1] || 1) - 1);
          return source.substring(start, start + Number(a[2] || source.length));
        }
        case "INSTR": {
          // INSTR(metin, aranan) ya da INSTR(baslangic, metin, aranan); S-247: baslangic eskiden metin sanilip yok sayiliyordu.
          const instrHasStart = a.length >= 3;
          const instrFrom = instrHasStart ? Math.max(1, Number(a[0] || 1)) : 1;
          const instrHay = String(a[instrHasStart ? 1 : 0] ?? "");
          const instrNeedle = String(a[instrHasStart ? 2 : 1] ?? "");
          return instrHay.indexOf(instrNeedle, instrFrom - 1) + 1;
        }
        case "LCASE": return String(a[0] ?? "").toLowerCase();
        case "UCASE": return String(a[0] ?? "").toUpperCase();
        case "LTRIM": return String(a[0] ?? "").replace(/^\s+/, "");
        case "RTRIM": return String(a[0] ?? "").replace(/\s+$/, "");
        case "TRIM": return String(a[0] ?? "").trim();
        case "SPACE": return " ".repeat(Number(a[0] || 0));
        case "STRING": {
          const count = Number(a[0]);
          if (!Number.isInteger(count) || count < 0 || count > 65535)
            return fail("UXB_STRING_COUNT", "STRING count must be between 0 and 65535");
          const code = typeof a[1] === "string" ? a[1].charCodeAt(0) : Number(a[1]);
          if (!Number.isInteger(code) || code < 0 || code > 255)
            return fail("UXB_STRING_CODE", "STRING char code range error or empty text");
          return String.fromCharCode(code).repeat(count);
        }
        case "HEX": return Math.trunc(Number(a[0] || 0)).toString(16).toUpperCase();
        case "OCT": return Math.trunc(Number(a[0] || 0)).toString(8);
        case "BIN": return Math.trunc(Number(a[0] || 0)).toString(2);
        case "ROL": return ((a[0] << a[1]) | (a[0] >>> (32 - a[1]))) | 0;
        case "ROR": return ((a[0] >>> a[1]) | (a[0] << (32 - a[1]))) | 0;
        case "POW": return Math.pow(Number(a[0] || 0), Number(a[1] || 0));
        case "BIGINIT": {
          const kind = String(a[0] ?? "").toUpperCase();
          const value = String(a[1] ?? "0");
          if (kind === "BIGI" || kind === "BIGINT") return BigInt(value);
          return fail("UXB_BIG_RUNTIME_REQUIRED", `BIGINIT ${kind} requires a real external precision runtime`);
        }
        default:
          return fail("UXB_JS_BUILTIN_UNSUPPORTED", `unsupported uXBasic builtin on JavaScript target: ${op}`);
      }
    },
  };

  uxb.data = {
    arrayNew(length = 0, fill = 0, lower = 0) {
      const arr = Array(Number(length) || 0).fill(fill);
      arr.__uxbLower = Number(lower) || 0;
      return arr;
    },
    arrayResize(array, length, fill = 0, lower = 0, preserve = false) {
      if (!Array.isArray(array)) return fail("UXB_ARRAY_TARGET_MISSING", "REDIM target is not an array");
      const n = Number(length), lo = Number(lower);
      if (!Number.isInteger(n) || n < 1 || n > 268435455) return fail("UXB_ARRAY_SIZE", "array invalid bounds or byte size overflow");
      const next = Array(n).fill(fill), oldLo = Number(array.__uxbLower) || 0;
      if (preserve) {
        const first = Math.max(lo, oldLo), last = Math.min(lo + n - 1, oldLo + array.length - 1);
        for (let i = first; i <= last; i++) next[i-lo] = array[i-oldLo];
      }
      // Preserve descriptor identity for forwarded array parameters.
      array.length = n;
      for (let i = 0; i < n; i++) array[i] = next[i];
      array.__uxbLower = lo;
      return array;
    },
    arrayLoad(array, index) {
      if (!array) return 0;
      const i = (Number(index) | 0) - (Number(array.__uxbLower) || 0);
      if (i < 0 || i >= array.length) return fail("UXB_ARRAY_INDEX", "array index out of bounds");
      return array[i] ?? 0;
    },
    arrayStore(array, index, value) {
      if (!array) return fail("UXB_ARRAY_TARGET_MISSING", "arrayStore target is missing");
      const i = (Number(index) | 0) - (Number(array.__uxbLower) || 0);
      if (i < 0 || i >= array.length) return fail("UXB_ARRAY_INDEX", "array index out of bounds");
      array[i] = value;
      return value;
    },
    arrayFieldRecord(array, index) {
      let record = this.arrayLoad(array, index);
      if (record === 0) { record = {}; this.arrayStore(array, index, record); }
      if (!record || typeof record !== "object") return fail("UXB_RECORD_ARRAY_TYPE", "inline record expected");
      return record;
    },
    arrayFieldLoad(array, index, field, offset, width, type) {
      const record = this.arrayFieldRecord(array, index);
      // Inline TYPE text fields contain immutable strings, not numeric union bytes.
      if (String(type).toUpperCase().replace(/^TYPE_/, "") === "STRING") return record[field] ?? "";
      return uxb.object.unionFieldLoad(record, field, offset, width, type);
    },
    arrayFieldStore(array, index, field, value, offset, width, type) {
      const record = this.arrayFieldRecord(array, index);
      if (String(type).toUpperCase().replace(/^TYPE_/, "") === "STRING") return record[field] = String(value);
      return uxb.object.unionFieldStore(record, field, value, offset, width, type);
    },
    // S-101: LBOUND/UBOUND of an array whose bounds exist only at run time (REDIM'd array,
    // `arr AS T[]` parameter). Compile-time bounds are folded to constants by the lowering.
    arrayLBound(array) {
      if (!Array.isArray(array)) return fail("UXB_ARRAY_TARGET_MISSING", "LBOUND target is not an array");
      return Number(array.__uxbLower) || 0;
    },
    arrayUBound(array) {
      if (!Array.isArray(array)) return fail("UXB_ARRAY_TARGET_MISSING", "UBOUND target is not an array");
      return (Number(array.__uxbLower) || 0) + array.length - 1;
    },
    memoryRefArray(array, elementBytes = 8) {
      if (!Array.isArray(array)) return fail("UXB_ARRAY_MEMORY_REF", "memoryRefArray requires an array");
      const w = Number(elementBytes)|0; if (![1,2,4,8].includes(w)) return fail("UXB_ARRAY_MEMORY_REF_WIDTH", `unsupported array memory width: ${w}`);
      return { __uxbMemoryRef: "ARRAY", array, elementBytes: w, byteLength: array.length*w };
    },
  };

  // Collections use stable runtime handles so generated JS, browser and
  // native-facing host calls share one LIST/DICT/SET contract.
  uxb.collections = {
    nextId: 1,
    values: new Map(),
    create(kind = "LIST") {
      const id = `c${this.nextId++}`;
      const k = String(kind || "LIST").toUpperCase();
      this.values.set(id, { kind: k, value: k === "DICT" ? new Map() : k === "SET" ? new Set() : [] });
      return id;
    },
    op(op, id, ...args) {
      const c = this.values.get(String(id));
      if (!c) return fail("UXB_COLLECTION_MISSING", `collection not found: ${id}`);
      const o = String(op || "").toUpperCase();
      if (c.kind === "LIST") {
        // S-652: degistirici islemler (ADD/PUSH/SET/REMOVE/CLEAR) basarida dilin DOGRU degeri -1'i dondurur (AST, MIR, x64 ile ayni);
        // gecersiz dizin AST ve MIR gibi calisma anı hatasidir.
        if (o === "ADD" || o === "PUSH") { c.value.push(args[0]); return -1; }
        if (o === "GET") return c.value[Number(args[0]) | 0];
        if (o === "SET") {
          const i = Number(args[0]) | 0;
          if (i < 0 || i >= c.value.length) return fail("UXB_COLLECTION_INDEX", "LIST index out of range");
          c.value[i] = args[1];
          return -1;
        }
        if (o === "REMOVE") {
          const i = Number(args[0]) | 0;
          if (i < 0 || i >= c.value.length) return fail("UXB_COLLECTION_INDEX", "LIST index out of range");
          c.value.splice(i, 1);
          return -1;
        }
        if (o === "CLEAR") { c.value.length = 0; return -1; }
        if (o === "LEN") return c.value.length;
      } else if (c.kind === "DICT") {
        if (o === "SET") { c.value.set(String(args[0]), args[1]); return -1; }
        if (o === "GET") return c.value.get(String(args[0]));
        if (o === "HAS") return c.value.has(String(args[0])) ? -1 : 0;   // S-569/S-246: dilde DOGRU = -1 (AST, MIR, x64 ile ayni)
        if (o === "CLEAR") { c.value.clear(); return -1; }
        if (o === "LEN") return c.value.size;
      } else if (c.kind === "SET") {
        if (o === "ADD") { c.value.add(args[0]); return -1; }
        if (o === "HAS") return c.value.has(args[0]) ? -1 : 0;   // S-569/S-246: dilde DOGRU = -1
        if (o === "REMOVE") { c.value.delete(args[0]); return -1; }
        if (o === "CLEAR") { c.value.clear(); return -1; }
        if (o === "LEN") return c.value.size;
      }
      return fail("UXB_COLLECTION_OP", `unsupported ${c.kind} operation: ${o}`);
    },
  };

  uxb.memory = {
    size: 1048576,
    bytes: new Uint8Array(1048576),
    _isRef(value) { return !!(value && typeof value === "object" && value.__uxbMemoryRef === "ARRAY"); },
    _arrayBytes(ref) { const a=ref.array,w=ref.elementBytes|0,out=new Uint8Array(a.length*w),dv=new DataView(out.buffer); for(let i=0;i<a.length;i++){const v=a[i]??0,p=i*w;if(w===1)out[p]=Number(v)&255;else if(w===2)dv.setUint16(p,Number(v)&65535,true);else if(w===4)dv.setUint32(p,Number(v)>>>0,true);else if(w===8)dv.setBigUint64(p,BigInt(v),true);} return out; },
    _writeArrayBytes(ref,bytes) { const a=ref.array,w=ref.elementBytes|0,dv=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength); for(let i=0;i<a.length&&i*w<bytes.byteLength;i++){const p=i*w;if(w===1)a[i]=bytes[p];else if(w===2)a[i]=dv.getUint16(p,true);else if(w===4)a[i]=dv.getUint32(p,true);else if(w===8)a[i]=dv.getBigUint64(p,true);} return 1; },
    _mode(mode) {
      const m = String(mode || "AUTO").toUpperCase();
      if (m === "NATIVE") return fail("UXB_JS_NATIVE_MEMORY_UNAVAILABLE", "native process memory is unavailable on JavaScript target");
      return m === "VIRTUAL" ? "VIRTUAL" : "AUTO";
    },
    _range(addr, count) {
      const a = Number(addr); const n = Number(count);
      if (!Number.isSafeInteger(a) || !Number.isSafeInteger(n) || a < 0 || n < 0 || a > this.size || n > this.size - a) return fail("UXB_MEMORY_RANGE", `memory range out of bounds: ${a}+${n}`);
      return a;
    },
    load(mode, addr, width) {
      this._mode(mode); const w = Number(width);
      if (this._isRef(addr)) { const b = this._arrayBytes(addr); const dv = new DataView(b.buffer); if (w === 1) return b[0] ?? 0; if (w === 2) return dv.getUint16(0, true); if (w === 4) return dv.getUint32(0, true); if (w === 8) return dv.getBigUint64(0, true); return fail("UXB_MEMORY_WIDTH", `unsupported memory load width: ${width}`); }
      const a = this._range(addr, w); const dv = new DataView(this.bytes.buffer);
      if (w === 1) return this.bytes[a];
      if (w === 2) return dv.getUint16(a, true);
      if (w === 4) return dv.getUint32(a, true);
      if (w === 8) return dv.getBigUint64(a, true);
      return fail("UXB_MEMORY_WIDTH", `unsupported memory load width: ${width}`);
    },
    store(mode, addr, value, width) {
      this._mode(mode); const w = Number(width);
      if (this._isRef(addr)) { const b = new Uint8Array(w); const dv = new DataView(b.buffer); if (w === 1) b[0] = Number(value) & 255; else if (w === 2) dv.setUint16(0, Number(value) & 65535, true); else if (w === 4) dv.setUint32(0, Number(value) >>> 0, true); else if (w === 8) dv.setBigUint64(0, BigInt(value), true); else return fail("UXB_MEMORY_WIDTH", `unsupported memory store width: ${width}`); return this._writeArrayBytes(addr, b); }
      const a = this._range(addr, w); const dv = new DataView(this.bytes.buffer);
      if (w === 1) this.bytes[a] = Number(value) & 255;
      else if (w === 2) dv.setUint16(a, Number(value) & 65535, true);
      else if (w === 4) dv.setUint32(a, Number(value) >>> 0, true);
      else if (w === 8) dv.setBigUint64(a, BigInt(value), true);
      else return fail("UXB_MEMORY_WIDTH", `unsupported memory store width: ${width}`);
      return 1;
    },
    copy(mode, src, dst, count, width) {
      this._mode(mode); const n=Number(count)*Number(width); if(this._isRef(src)||this._isRef(dst)){const tmp=this._isRef(src)?this._arrayBytes(src).slice(0,n):this.bytes.slice(this._range(src,n),this._range(src,n)+n);if(this._isRef(dst))return this._writeArrayBytes(dst,tmp);const d=this._range(dst,n);this.bytes.set(tmp,d);return 1;} const s0=this._range(src,n),d0=this._range(dst,n);this.bytes.copyWithin(d0,s0,s0+n);return 1;
    },
    fill(mode, dst, value, count, width) {
      this._mode(mode); const w = Number(width); const n = Number(count); const total = n * w;
      if (this._isRef(dst)) { const b = new Uint8Array(total); const dv = new DataView(b.buffer); for (let i = 0; i < n; i++) { const p = i * w; if (w === 1) b[p] = Number(value) & 255; else if (w === 2) dv.setUint16(p, Number(value) & 65535, true); else if (w === 4) dv.setUint32(p, Number(value) >>> 0, true); else return fail("UXB_MEMORY_WIDTH", `unsupported memory fill width: ${width}`); } return this._writeArrayBytes(dst, b); }
      const d = this._range(dst, total); const dv = new DataView(this.bytes.buffer); const v = Number(value);
      for (let i = 0; i < n; i++) { const p = d + i * w; if (w === 1) this.bytes[p] = v & 255; else if (w === 2) dv.setUint16(p, v & 65535, true); else if (w === 4) dv.setUint32(p, v >>> 0, true); else return fail("UXB_MEMORY_WIDTH", `unsupported memory fill width: ${width}`); }
      return n;
    },
    readSequence(mode, addr, length) {
      this._mode(mode); const n = Number(length); const a = this._range(addr, n); let out = ""; for (let i = 0; i < n; i++) out += String.fromCharCode(this.bytes[a + i]); return out;
    },
    writeSequence(mode, dst, source, length) {
      this._mode(mode); const text = String(source ?? ""); const n = Number(length); if (!Number.isSafeInteger(n) || n < 0 || n > text.length) return fail("UXB_MEMORY_SEQUENCE_LENGTH", "sequence length exceeds source string length"); const d = this._range(dst, n); for (let i = 0; i < n; i++) this.bytes[d + i] = text.charCodeAt(i) & 255; return 1;
    },
  };

  uxb.object = {
    classes: new Map(),
    unions: new Map(),
    recordBytes: new WeakMap(),
    async create(className = "OBJECT", ...args) {
      const name = String(className || "OBJECT").toUpperCase();
      const spec = this.classes.get(name);
      if (!spec) return fail("UXB_CLASS_NOT_REGISTERED", name);
      const object = { __uxbClass: name, __uxbVTable: spec.slots.slice() };
      // S-485 / S-487 (P0.2): only the constructor of the class being created runs here; the base constructors are called from inside its body
      // (the front end writes `SUPER.CONSTRUCTOR(args)` as its first statement), so every engine runs the same chain.
      const construct = async (key) => { const cur = this.classes.get(String(key).toUpperCase()); if (!cur) return fail("UXB_CLASS_NOT_REGISTERED", key); if (cur.ctor) { const fn = uxb.exports[cur.ctor]; if (typeof fn !== "function") return fail("UXB_CONSTRUCTOR_NOT_FOUND", cur.ctor); await fn(object, ...args.slice(0, cur.ctorParamCount)); } };
      await construct(name);
      return object;
    },
    registerClass(className, slots = [], ctor = "", dtor = "", base = "", ctorParamCount = 0) {
      this.classes.set(String(className || "OBJECT").toUpperCase(), {slots: Array.isArray(slots) ? slots.slice() : [], ctor: String(ctor || "").toUpperCase(), dtor: String(dtor || "").toUpperCase(), base: String(base || "").toUpperCase(), ctorParamCount: Math.max(0, Number(ctorParamCount)|0)});
      return 1;
    },
    // S-574 (2026-10-17): a DELETEd object (`__uxbDeleted`, set by `delete` below) is the same error as a NULL reference in field and method access.
    fieldLoad(object, key, dflt = 0) {
      // S-573: reading a field of a NULL / DELETEd class reference used to return `undefined` silently
      // (AST, MIR, x64 and the legacy backend stop with "field access on a null object reference").
      if (!object || object.__uxbDeleted) return fail("UXB_OBJECT_TARGET_MISSING", "fieldLoad target is missing (field access on a null object reference)");
      // S-598: a field that was never written reads as the zero value of its type (AST, MIR, native x64, WASM and legacy x64 allocate
      // zero-filled objects); a JS object starts empty, so the emitter passes the typed default. Without it `x.n = x.n + 1` was NaN.
      const v = object[key];
      return v === undefined ? dflt : v;
    },
    fieldStore(object, key, value) {
      if (!object || object.__uxbDeleted) return fail("UXB_OBJECT_TARGET_MISSING", "fieldStore target is missing (field access on a null object reference)");
      object[key] = value;
      return value;
    },
    unionFieldLoad(root, field, offset, width, type) {
      const isRecord = root !== null && typeof root === "object";
      const rootKey = isRecord ? root : String(root || "").toUpperCase();
      const off = Number(offset) | 0;
      const w = Number(width) | 0;
      const t = String(type || "").toUpperCase().replace(/^TYPE_/, "");
      if (!rootKey || !String(field || "") || off < 0 || ![1, 2, 4, 8].includes(w) || (!isRecord && off + w > 256)) return fail("UXB_UNION_FIELD_RANGE", "invalid UNION field range");
      const buffers = isRecord ? this.recordBytes : this.unions;
      let bytes = buffers.get(rootKey);
      if (!bytes || bytes.byteLength < off + w) {
        const grown = new ArrayBuffer(isRecord ? off + w : 256);
        if (bytes) new Uint8Array(grown).set(new Uint8Array(bytes));
        buffers.set(rootKey, bytes = grown);
      }
      const dv = new DataView(bytes);
      if (t === "F32" || t === "SINGLE") { if (w !== 4) return fail("UXB_UNION_FIELD_TYPE", "F32 UNION field must be 4 bytes"); return dv.getFloat32(off, true); }
      if (t === "F64" || t === "DOUBLE") { if (w !== 8) return fail("UXB_UNION_FIELD_TYPE", "F64 UNION field must be 8 bytes"); return dv.getFloat64(off, true); }
      if (t === "I8" || t === "BYTE" || t === "SBYTE") return w === 1 ? dv.getInt8(off) : fail("UXB_UNION_FIELD_TYPE", "I8 UNION field must be 1 byte");
      if (t === "I16" || t === "SHORT") return w === 2 ? dv.getInt16(off, true) : fail("UXB_UNION_FIELD_TYPE", "I16 UNION field must be 2 bytes");
      if (t === "I32" || t === "INTEGER" || t === "INT" || t === "LONG") return w === 4 ? dv.getInt32(off, true) : fail("UXB_UNION_FIELD_TYPE", "I32 UNION field must be 4 bytes");
      if (t === "U8" || t === "UBYTE" || t === "BOOLEAN" || t === "BOOL") return w === 1 ? dv.getUint8(off) : fail("UXB_UNION_FIELD_TYPE", "U8 UNION field must be 1 byte");
      if (t === "U16" || t === "USHORT") return w === 2 ? dv.getUint16(off, true) : fail("UXB_UNION_FIELD_TYPE", "U16 UNION field must be 2 bytes");
      if (t === "U32" || t === "UINTEGER" || t === "UINT" || t === "ULONG") return w === 4 ? dv.getUint32(off, true) : fail("UXB_UNION_FIELD_TYPE", "U32 UNION field must be 4 bytes");
      if (t === "I64" || t === "LONGINT") return w === 8 ? dv.getBigInt64(off, true) : fail("UXB_UNION_FIELD_TYPE", "I64 UNION field must be 8 bytes");
      if (t === "U64" || t === "ULONGINT") return w === 8 ? dv.getBigUint64(off, true) : fail("UXB_UNION_FIELD_TYPE", "U64 UNION field must be 8 bytes");
      return fail("UXB_UNION_FIELD_TYPE", `unsupported UNION field type: ${type}`);
    },
    unionFieldStore(root, field, value, offset, width, type) {
      const isRecord = root !== null && typeof root === "object";
      const rootKey = isRecord ? root : String(root || "").toUpperCase();
      const off = Number(offset) | 0;
      const w = Number(width) | 0;
      const t = String(type || "").toUpperCase().replace(/^TYPE_/, "");
      if (!rootKey || !String(field || "") || off < 0 || ![1, 2, 4, 8].includes(w) || (!isRecord && off + w > 256)) return fail("UXB_UNION_FIELD_RANGE", "invalid UNION field range");
      const buffers = isRecord ? this.recordBytes : this.unions;
      let bytes = buffers.get(rootKey);
      if (!bytes || bytes.byteLength < off + w) {
        const grown = new ArrayBuffer(isRecord ? off + w : 256);
        if (bytes) new Uint8Array(grown).set(new Uint8Array(bytes));
        buffers.set(rootKey, bytes = grown);
      }
      const dv = new DataView(bytes);
      const n = Number(value);
      if (t === "F32" || t === "SINGLE") { if (w !== 4) return fail("UXB_UNION_FIELD_TYPE", "F32 UNION field must be 4 bytes"); dv.setFloat32(off, n, true); return value; }
      if (t === "F64" || t === "DOUBLE") { if (w !== 8) return fail("UXB_UNION_FIELD_TYPE", "F64 UNION field must be 8 bytes"); dv.setFloat64(off, n, true); return value; }
      if (t === "I8" || t === "BYTE" || t === "SBYTE") { if (w !== 1) return fail("UXB_UNION_FIELD_TYPE", "I8 UNION field must be 1 byte"); dv.setInt8(off, n); return value; }
      if (t === "I16" || t === "SHORT") { if (w !== 2) return fail("UXB_UNION_FIELD_TYPE", "I16 UNION field must be 2 bytes"); dv.setInt16(off, n, true); return value; }
      if (t === "I32" || t === "INTEGER" || t === "INT" || t === "LONG") { if (w !== 4) return fail("UXB_UNION_FIELD_TYPE", "I32 UNION field must be 4 bytes"); dv.setInt32(off, n, true); return value; }
      if (t === "U8" || t === "UBYTE" || t === "BOOLEAN" || t === "BOOL") { if (w !== 1) return fail("UXB_UNION_FIELD_TYPE", "U8 UNION field must be 1 byte"); dv.setUint8(off, n); return value; }
      if (t === "U16" || t === "USHORT") { if (w !== 2) return fail("UXB_UNION_FIELD_TYPE", "U16 UNION field must be 2 bytes"); dv.setUint16(off, n, true); return value; }
      if (t === "U32" || t === "UINTEGER" || t === "UINT" || t === "ULONG") { if (w !== 4) return fail("UXB_UNION_FIELD_TYPE", "U32 UNION field must be 4 bytes"); dv.setUint32(off, n, true); return value; }
      if (t === "I64" || t === "LONGINT") { if (w !== 8) return fail("UXB_UNION_FIELD_TYPE", "I64 UNION field must be 8 bytes"); dv.setBigInt64(off, typeof value === "bigint" ? value : BigInt(Math.trunc(n)), true); return value; }
      if (t === "U64" || t === "ULONGINT") { if (w !== 8) return fail("UXB_UNION_FIELD_TYPE", "U64 UNION field must be 8 bytes"); dv.setBigUint64(off, typeof value === "bigint" ? value : BigInt(Math.trunc(n)), true); return value; }
      return fail("UXB_UNION_FIELD_TYPE", `unsupported UNION field type: ${type}`);
    },
    async callStaticMethod(target, args = []) {
      const fn = uxb.exports[String(target).toUpperCase()];
      if (typeof fn !== "function") return fail("UXB_STATIC_METHOD_NOT_FOUND", target);
      return await fn(...(Array.isArray(args) ? args : []));
    },
    async callMethod(object, target, args = []) {
      if (!object || object.__uxbDeleted) return fail("UXB_OBJECT_TARGET_MISSING", "callMethod target is missing (method call on a null object reference)");
      const fn = uxb.exports[String(target).toUpperCase()];
      if (typeof fn !== "function") return fail("UXB_METHOD_NOT_FOUND", `method not found: ${target}`);
      return await fn(object, ...(Array.isArray(args) ? args : []));
    },
    async virtualCall(object, slot, args = []) {
      if (!object || object.__uxbDeleted) return fail("UXB_OBJECT_TARGET_MISSING", "virtualCall target is missing (method call on a null object reference)");
      const index = Number(slot) | 0;
      const target = object.__uxbVTable && object.__uxbVTable[index];
      if (!target) return fail("UXB_VTABLE_SLOT_MISSING", `vtable slot ${index} is not bound for ${object.__uxbClass}`);
      const fn = uxb.exports[String(target).toUpperCase()];
      if (typeof fn !== "function") return fail("UXB_METHOD_NOT_FOUND", `vtable target not found: ${target}`);
      return await fn(object, ...(Array.isArray(args) ? args : []));
    },
    async delete(object) {
      // S-616: a DELETE of the same object from inside its own destructor does nothing (the chain is already running).
      if (!object || object.__uxbDeleted || object.__uxbDestroying) return 0;
      object.__uxbDestroying = true;
      const destroy = async (key) => { const cur = this.classes.get(String(key).toUpperCase()); if (!cur) return fail("UXB_CLASS_NOT_REGISTERED", key); if (cur.dtor) { const fn = uxb.exports[cur.dtor]; if (typeof fn !== "function") return fail("UXB_DESTRUCTOR_NOT_FOUND", cur.dtor); await fn(object); } if (cur.base) await destroy(cur.base); };
      await destroy(object.__uxbClass); object.__uxbDeleted = true; object.__uxbDestroying = false; return 0;
    },
  };

  uxb.canvas = {
    screen(width = 800, height = 600) {
      if (typeof globalObject.document === "undefined") {
        return fail("UXB_BROWSER_DOM_REQUIRED", "SCREEN requires a browser DOM provider");
      }
      let canvas = globalObject.document.getElementById("ux-canvas");
      if (!canvas) {
        canvas = globalObject.document.createElement("canvas");
        canvas.id = "ux-canvas";
        globalObject.document.body.appendChild(canvas);
      }
      canvas.width = Number(width) || 800;
      canvas.height = Number(height) || 600;
      state.canvas = canvas;
      state.ctx = canvas.getContext("2d");
      if (!state.ctx) return fail("UXB_CANVAS2D_UNAVAILABLE", "Canvas2D context is unavailable");
      return canvas;
    },
    clear() {
      if (state.ctx && state.canvas) state.ctx.clearRect(0, 0, state.canvas.width, state.canvas.height);
      return 0;
    },
    fillRect(x, y, width, height) {
      if (!state.ctx) uxb.canvas.screen();
      state.ctx.fillRect(Number(x) || 0, Number(y) || 0, Number(width) || 0, Number(height) || 0);
      return 0;
    },
    text(x, y, value) {
      if (!state.ctx) uxb.canvas.screen();
      state.ctx.fillText(String(value ?? ""), Number(x) || 0, Number(y) || 0);
      return 0;
    },
  };

  uxb.json = {
    parse(text) {
      return JSON.parse(String(text));
    },
    stringify(value, space = 0) {
      return JSON.stringify(value, (_key, item) => {
        if (typeof item === "bigint") return { $uxbType: "bigint", value: item.toString() };
        return item;
      }, space);
    },
  };

  uxb.host = {
    _call: null,
    install(callFunction) {
      if (typeof callFunction !== "function") return fail("UXB_BAD_HOST_PROVIDER", "host provider must be a function");
      uxb.host._call = callFunction;
      return 1;
    },
    async call(name, args = []) {
      const normalized = String(name || "").toUpperCase();
      switch (normalized) {
        case "SCREEN": return uxb.canvas.screen(args[0], args[1]);
        case "CLS": uxb.console.clear(); return uxb.canvas.clear();
        case "FILLRECT": return uxb.canvas.fillRect(args[0], args[1], args[2], args[3]);
        case "TEXT": return uxb.canvas.text(args[0], args[1], args[2]);
        case "LIST_NEW": return uxb.collections.create("LIST");
        case "DICT_NEW": return uxb.collections.create("DICT");
        case "SET_NEW": return uxb.collections.create("SET");
        case "LISTADD": return uxb.collections.op("ADD", args[0], args[1]);
        case "LISTGET": return uxb.collections.op("GET", args[0], args[1]);
        case "LISTSET": return uxb.collections.op("SET", args[0], args[1], args[2]);
        case "LISTREMOVE": return uxb.collections.op("REMOVE", args[0], args[1]);
        case "LISTCLEAR": return uxb.collections.op("CLEAR", args[0]);
        case "LISTLEN": return uxb.collections.op("LEN", args[0]);
        case "DICTSET": return uxb.collections.op("SET", args[0], args[1], args[2]);
        case "DICTGET": return uxb.collections.op("GET", args[0], args[1]);
        case "DICTHAS": return uxb.collections.op("HAS", args[0], args[1]);
        case "DICTCLEAR": return uxb.collections.op("CLEAR", args[0]);
        case "DICTLEN": return uxb.collections.op("LEN", args[0]);
        case "SETADD": return uxb.collections.op("ADD", args[0], args[1]);
        case "SETHAS": return uxb.collections.op("HAS", args[0], args[1]);
        case "SETREMOVE": return uxb.collections.op("REMOVE", args[0], args[1]);
        case "SETCLEAR": return uxb.collections.op("CLEAR", args[0]);
        case "SETLEN": return uxb.collections.op("LEN", args[0]);
        case "PROGRAM_END": {
          // S-538: END inside a SUB/FUNCTION ends the whole program. The signal unwinds every awaiting routine up to the
          // entry point, whose catch handler treats it as a normal end (no message, exit status 0).
          const programEnd = new Error("UXB_PROGRAM_END");
          programEnd.uxbProgramEnd = true;
          throw programEnd;
        }
        default:
          if (typeof uxb.host._call !== "function") {
            return fail("UXB_HOST_BINDING_MISSING", `UXB host binding missing: ${name}`);
          }
          return await uxb.host._call(String(name), Array.isArray(args) ? args : []);
      }
    },
  };

  uxb.input.prompt = async (...args) => await uxb.host.call("INPUT_PROMPT", args);

  const compat = {
    get out() { return state.out; },
    get pending() { return state.pending; },
    set pending(value) { state.pending = String(value ?? ""); },
    get channel() { return state.channel; },
    set channel(value) { state.channel = String(value ?? "screen"); },
    get cursor() { return state.cursor; },
    get colorState() { return state.colorState; },
    get seed() { return state.seed; },
    get canvas() { return state.canvas; },
    get ctx() { return state.ctx; },
    get wasm() { return uxb.wasm.instance || null; },
    set wasm(value) { uxb.wasm.instance = value; },
    print: (...args) => uxb.console.print(...args),
    println: (...args) => uxb.console.println(...args),
    printSeparator: kind => uxb.console.separator(kind),
    formatF32: value => uxb.console.formatF32(value),
    input: async (...args) => await uxb.input.prompt(...args),
    cls: () => { uxb.console.clear(); return uxb.canvas.clear(); },
    color: (...args) => { state.colorState = args; return 0; },
    locate: (row, col) => {
      state.cursor = { row: Math.max(1, Math.trunc(Number(row) || 1)), col: Math.max(1, Math.trunc(Number(col) || 1)) };
      state.printColumn = state.cursor.col - 1;
      if (state.sink && typeof state.sink.locate === "function") state.sink.locate(state.cursor.row, state.cursor.col);
      else if (typeof process !== "undefined" && process.stdout?.isTTY) process.stdout.write(`\x1b[${state.cursor.row};${state.cursor.col}H`);
      return 0;
    },
    randomize: value => uxb.random.seed(value),
    rnd: () => uxb.random.next(),
    typeOf: value => uxb.lang.typeOf(value),
    sizeOf: name => uxb.lang.sizeOf(name),
    offsetOf: (...args) => uxb.lang.offsetOf(...args),
    pointerOf: (...args) => uxb.lang.pointerOf(...args),
    arrayNew: (...args) => uxb.data.arrayNew(...args),
    arrayResize: (...args) => uxb.data.arrayResize(...args),
    arrayLoad: (...args) => uxb.data.arrayLoad(...args),
    arrayStore: (...args) => uxb.data.arrayStore(...args),
    arrayFieldLoad: (...args) => uxb.data.arrayFieldLoad(...args),
    arrayFieldStore: (...args) => uxb.data.arrayFieldStore(...args),
    arrayLBound: (...args) => uxb.data.arrayLBound(...args),
    arrayUBound: (...args) => uxb.data.arrayUBound(...args),
    memoryRefArray: (...args) => uxb.data.memoryRefArray(...args),
    memoryLoad: (...args) => uxb.memory.load(...args),
    memoryStore: (...args) => uxb.memory.store(...args),
    memoryCopy: (...args) => uxb.memory.copy(...args),
    memoryFill: (...args) => uxb.memory.fill(...args),
    memoryReadSequence: (...args) => uxb.memory.readSequence(...args),
    memoryWriteSequence: (...args) => uxb.memory.writeSequence(...args),
    objectNew: (...args) => uxb.object.create(...args),
    fieldLoad: (...args) => uxb.object.fieldLoad(...args),
    fieldStore: (...args) => uxb.object.fieldStore(...args),
    unionFieldLoad: (...args) => uxb.object.unionFieldLoad(...args),
    unionFieldStore: (...args) => uxb.object.unionFieldStore(...args),
    registerClass: (...args) => uxb.object.registerClass(...args),
    callStaticMethod: (...args) => uxb.object.callStaticMethod(...args),
    callMethod: (...args) => uxb.object.callMethod(...args),
    virtualCall: (...args) => uxb.object.virtualCall(...args),
    objectDelete: (...args) => uxb.object.delete(...args),
    screen: (...args) => uxb.canvas.screen(...args),
    fillRect: (...args) => uxb.canvas.fillRect(...args),
    text: (...args) => uxb.canvas.text(...args),
    builtin: (...args) => uxb.lang.builtin(...args),
    callHost: async (...args) => await uxb.host.call(...args),
  };

  Object.defineProperty(uxb, "compat", { value: compat, enumerable: false, configurable: false, writable: false });
  Object.defineProperty(globalObject, "uxb", { value: uxb, enumerable: true, configurable: true, writable: false });

  // Temporary migration bridge. New generated code must bind through globalThis.uxb.
  if (!globalObject.ux) globalObject.ux = compat;
})(globalThis);
