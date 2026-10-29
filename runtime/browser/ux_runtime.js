// uXBasic Browser Runtime - matrix aware runtime
// This runtime is intentionally host-side: browser APIs, async I/O, canvas, audio,
// AI, file pickers, serial/bluetooth and fallback builtins live here.
// Generated JS and MIR executor both call this object.

import { UXB_SURFACE_REGISTRY } from "./ux_surface_registry.js";

function toNumber(v) {
  if (v === null || v === undefined || v === "") return 0;
  if (typeof v === "number") return v;
  if (typeof v === "boolean") return v ? 1 : 0;
  const n = Number(v);
  return Number.isNaN(n) ? 0 : n;
}

function toStringValue(v) {
  if (v === null || v === undefined) return "";
  return String(v);
}

function upperName(v) {
  return String(v ?? "").toUpperCase();
}

class UxbDiagnostic extends Error {
  constructor(message, code = "UXB_DIAGNOSTIC") {
    super(message);
    this.name = "UxbDiagnostic";
    this.code = code;
  }
}

export const ux = {
  version: "uxb-browser-runtime-matrix-v1",
  registry: UXB_SURFACE_REGISTRY,
  vars: Object.create(null),
  globals: Object.create(null),
  outputBuffer: "",
  canvas: null,
  ctx: null,
  keys: new Set(),
  mouse: {x: 0, y: 0, buttons: new Set()},
  sprites: new Map(),
  spriteSheets: new Map(),
  animations: new Map(),
  wasm: null,
  files: new Map(),
  collections: new Map(),
  objects: new Map(),
  eventBus: new EventTarget(),
  randomSeed: 123456789,
  aiConfig: {backend: "auto", systemPrompt: "Türkçe yanıt ver."},
  ffiEndpoint: null,
  diagCounts: new Map(),
  memoryBytes: new Map(),
  memorySize: 1048576,
  symbolPtrs: new Map(),
  nextPtr: 4096,

  diag(message, code = "UXB_DIAGNOSTIC") {
    const line = `[${code}] ${message}`;
    const key = `${code}|${message}`;
    const count = (this.diagCounts.get(key) ?? 0) + 1;
    this.diagCounts.set(key, count);
    if (count <= 10) {
      console.warn(line);
    } else if (count === 11) {
      console.warn(`[${code}] aynı tanı mesajı tekrar ettiği için bastırılıyor`);
    }
    return {ok: false, code, message, count};
  },

  fail(message, code = "UXB_ERROR") {
    throw new UxbDiagnostic(message, code);
  },

  print(value = "") {
    const text = toStringValue(value);
    this.outputBuffer += text + "\n";
    console.log(text);
    const out = document.getElementById("ux-output");
    if (out) out.textContent += text + "\n";
    return text.length;
  },

  printRaw(value = "") {
    const text = toStringValue(value);
    this.outputBuffer += text;
    console.log(text);
    const out = document.getElementById("ux-output");
    if (out) out.textContent += text;
    return text.length;
  },

  println() {
    this.outputBuffer += "\n";
    const out = document.getElementById("ux-output");
    if (out) out.textContent += "\n";
    return 1;
  },

  input(promptText = "") {
    return globalThis.prompt ? globalThis.prompt(promptText) ?? "" : "";
  },

  locate(row, col) {
    this.globals.__cursorRow = toNumber(row);
    this.globals.__cursorCol = toNumber(col);
  },

  color(fg, bg = null) {
    this.globals.__colorFg = fg;
    this.globals.__colorBg = bg;
    if (this.ctx) {
      this.ctx.fillStyle = fg;
      this.ctx.strokeStyle = fg;
    }
  },

  screen(width = 800, height = 600) {
    let canvas = document.getElementById("ux-canvas");
    if (!canvas) {
      canvas = document.createElement("canvas");
      canvas.id = "ux-canvas";
      document.body.appendChild(canvas);
    }
    canvas.width = toNumber(width);
    canvas.height = toNumber(height);
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    canvas.addEventListener("mousemove", e => {
      const r = canvas.getBoundingClientRect();
      this.mouse.x = e.clientX - r.left;
      this.mouse.y = e.clientY - r.top;
    });
    canvas.addEventListener("mousedown", e => this.mouse.buttons.add(e.button));
    canvas.addEventListener("mouseup", e => this.mouse.buttons.delete(e.button));
    return canvas;
  },

  cls() {
    if (!this.ctx || !this.canvas) return;
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
  },

  line(x1, y1, x2, y2) {
    if (!this.ctx) this.screen();
    this.ctx.beginPath();
    this.ctx.moveTo(toNumber(x1), toNumber(y1));
    this.ctx.lineTo(toNumber(x2), toNumber(y2));
    this.ctx.stroke();
  },

  rect(x, y, w, h) {
    if (!this.ctx) this.screen();
    this.ctx.strokeRect(toNumber(x), toNumber(y), toNumber(w), toNumber(h));
  },

  fillRect(x, y, w, h) {
    if (!this.ctx) this.screen();
    this.ctx.fillRect(toNumber(x), toNumber(y), toNumber(w), toNumber(h));
  },

  circle(x, y, r) {
    if (!this.ctx) this.screen();
    this.ctx.beginPath();
    this.ctx.arc(toNumber(x), toNumber(y), toNumber(r), 0, Math.PI * 2);
    this.ctx.stroke();
  },

  text(x, y, value) {
    if (!this.ctx) this.screen();
    this.ctx.fillText(toStringValue(value), toNumber(x), toNumber(y));
  },

  async loadSprite(id, path) {
    const img = new Image();
    img.src = path;
    await img.decode();
    this.sprites.set(String(id), img);
    return img;
  },

  drawSprite(id, x, y, w = null, h = null) {
    if (!this.ctx) this.screen();
    const img = this.sprites.get(String(id));
    if (!img) return this.diag(`Sprite bulunamadı: ${id}`, "UXB_SPRITE_MISSING");
    if (w === null || h === null) this.ctx.drawImage(img, toNumber(x), toNumber(y));
    else this.ctx.drawImage(img, toNumber(x), toNumber(y), toNumber(w), toNumber(h));
  },

  loadSheet(id, path, frameW, frameH) {
    return this.loadSprite(id, path).then(img => {
      this.spriteSheets.set(String(id), {img, frameW: toNumber(frameW), frameH: toNumber(frameH)});
      return img;
    });
  },

  drawFrame(id, frame, x, y, w = null, h = null) {
    if (!this.ctx) this.screen();
    const sh = this.spriteSheets.get(String(id));
    if (!sh) return this.diag(`Sprite sheet bulunamadı: ${id}`, "UXB_SHEET_MISSING");
    const cols = Math.max(1, Math.floor(sh.img.width / sh.frameW));
    const f = toNumber(frame);
    const sx = (f % cols) * sh.frameW;
    const sy = Math.floor(f / cols) * sh.frameH;
    this.ctx.drawImage(sh.img, sx, sy, sh.frameW, sh.frameH, toNumber(x), toNumber(y), w ?? sh.frameW, h ?? sh.frameH);
  },

  flip() {
    // Canvas2D immediate-mode backend has no swapchain. Kept for BASIC compatibility.
  },

  keyDown(key) {
    return this.keys.has(String(key).toUpperCase()) ? 1 : 0;
  },

  mouseX() { return this.mouse.x; },
  mouseY() { return this.mouse.y; },
  mouseDown(button = 0) { return this.mouse.buttons.has(toNumber(button)) ? 1 : 0; },

  rnd() {
    // LCG deterministic fallback.
    this.randomSeed = (1103515245 * this.randomSeed + 12345) >>> 0;
    return (this.randomSeed & 0x7fffffff) / 0x80000000;
  },

  randomize(seed = Date.now()) {
    this.randomSeed = toNumber(seed) >>> 0;
  },

  // Numeric/string builtins
  math(name, ...args) {
    const n = name.toUpperCase();
    const a0 = toNumber(args[0]);
    switch (n) {
      case "ABS": return Math.abs(a0);
      case "INT": return Math.floor(a0);
      case "FIX": return a0 < 0 ? Math.ceil(a0) : Math.floor(a0);
      case "SGN": return a0 < 0 ? -1 : a0 > 0 ? 1 : 0;
      case "SQR": return Math.sqrt(a0);
      case "SIN": return Math.sin(a0);
      case "COS": return Math.cos(a0);
      case "TAN": return Math.tan(a0);
      case "ATN": return Math.atan(a0);
      case "EXP": return Math.exp(a0);
      case "LOG": return Math.log(a0);
      case "RND": return this.rnd();
      case "RANDOMIZE": return this.randomize(a0);
      case "VAL": return Number.parseFloat(toStringValue(args[0])) || 0;
      case "CINT": return Math.trunc(a0);
      case "CLNG": return Math.trunc(a0);
      case "CDBL": return Number(a0);
      case "CSNG": return Number(a0);
      default: return this.diag(`Math builtin eksik: ${name}`, "UXB_MATH_MISSING");
    }
  },

  string(name, ...args) {
    const n = name.toUpperCase();
    const s = toStringValue(args[0]);
    switch (n) {
      case "LEN": return s.length;
      case "ASC": return s.length ? s.charCodeAt(0) : 0;
      case "CHR": return String.fromCharCode(toNumber(args[0]));
      case "STR": return String(args[0]);
      case "UCASE": return s.toUpperCase();
      case "LCASE": return s.toLowerCase();
      case "LTRIM": return s.replace(/^\s+/, "");
      case "RTRIM": return s.replace(/\s+$/, "");
      case "MID": {
        const start = Math.max(1, toNumber(args[1] ?? 1));
        const len = args.length >= 3 ? toNumber(args[2]) : undefined;
        return len === undefined ? s.substring(start - 1) : s.substring(start - 1, start - 1 + len);
      }
      case "SPACE": return " ".repeat(Math.max(0, toNumber(args[0])));
      case "STRING": return toStringValue(args[1] ?? " ").repeat(Math.max(0, toNumber(args[0])));
      default: return this.diag(`String builtin eksik: ${name}`, "UXB_STRING_MISSING");
    }
  },

  collectionNew(kind = "LIST") {
    const id = "c" + (this.collections.size + 1);
    const k = String(kind).toUpperCase();
    const value = k === "DICT" ? new Map() : k === "SET" ? new Set() : [];
    this.collections.set(id, {kind: k, value});
    return id;
  },

  collectionOp(op, id, ...args) {
    const c = this.collections.get(String(id));
    if (!c) return this.diag(`Koleksiyon bulunamadı: ${id}`, "UXB_COLLECTION_MISSING");
    const opu = String(op).toUpperCase();
    if (c.kind === "LIST") {
      if (opu === "PUSH" || opu === "ADD") return c.value.push(args[0]);
      if (opu === "GET") return c.value[toNumber(args[0])];
      if (opu === "SET") { c.value[toNumber(args[0])] = args[1]; return args[1]; }
      if (opu === "REMOVE") {
        const i = toNumber(args[0]);
        if (i < 0 || i >= c.value.length) return null;
        return c.value.splice(i, 1)[0] ?? null;
      }
      if (opu === "CLEAR") { c.value.length = 0; return 0; }
      if (opu === "LEN") return c.value.length;
    }
    if (c.kind === "DICT") {
      if (opu === "SET") { c.value.set(String(args[0]), args[1]); return args[1]; }
      if (opu === "GET") return c.value.get(String(args[0]));
      if (opu === "HAS") return c.value.has(String(args[0])) ? -1 : 0;   // S-569/S-246: dilde DOGRU = -1
      if (opu === "CLEAR") { c.value.clear(); return 0; }
      if (opu === "FINDKEY") {
        for (const [k, v] of c.value.entries()) {
          if (v === args[0]) return k;
        }
        return "";
      }
      if (opu === "LEN") return c.value.size;
    }
    if (c.kind === "SET") {
      if (opu === "ADD") { c.value.add(args[0]); return c.value.size; }
      if (opu === "HAS") return c.value.has(args[0]) ? -1 : 0;   // S-569/S-246: dilde DOGRU = -1
      if (opu === "REMOVE") return c.value.delete(args[0]) ? 1 : 0;
      if (opu === "CLEAR") { c.value.clear(); return 0; }
      if (opu === "FIND") return c.value.has(args[0]) ? args[0] : null;
      if (opu === "LEN") return c.value.size;
    }
    return this.diag(`Koleksiyon işlemi eksik: ${c.kind}.${op}`, "UXB_COLLECTION_OP_MISSING");
  },

  normalizeHostName(name) {
    let n = upperName(name);
    if (!n) return "";
    if (n.endsWith("_STMT")) n = n.slice(0, -5);
    if (n.endsWith("_EXPR")) n = n.slice(0, -5);
    return n;
  },

  setStringSize(value) {
    const n = Math.max(0, toNumber(value));
    this.globals.__stringSize = n;
    return n;
  },

  setVarValue(name, value) {
    const key = String(name ?? "");
    if (!key) return value;
    this.vars[key] = value;
    this.globals[key] = value;
    this.globals[key.toUpperCase()] = value;
    return value;
  },

  getVarValue(name, fallback = 0) {
    const key = String(name ?? "");
    if (!key) return fallback;
    if (Object.prototype.hasOwnProperty.call(this.vars, key)) return this.vars[key];
    if (Object.prototype.hasOwnProperty.call(this.vars, key.toUpperCase())) return this.vars[key.toUpperCase()];
    if (Object.prototype.hasOwnProperty.call(this.globals, key)) return this.globals[key];
    if (Object.prototype.hasOwnProperty.call(this.globals, key.toUpperCase())) return this.globals[key.toUpperCase()];
    return fallback;
  },

  allocPointer(symbolHint = "") {
    const key = upperName(symbolHint);
    if (key && this.symbolPtrs.has(key)) return this.symbolPtrs.get(key);
    const ptr = this.nextPtr;
    this.nextPtr += 256;
    if (key) this.symbolPtrs.set(key, ptr);
    return ptr;
  },

  resolveMemoryMode(mode = "AUTO") {
    const m = upperName(mode || "AUTO");
    if (m === "NATIVE") return this.diag("native process memory is unavailable in browser runtime", "UXB_NATIVE_MEMORY_UNAVAILABLE");
    return m === "VIRTUAL" ? "VIRTUAL" : "AUTO";
  },

  memoryRange(addr, count) {
    const a = toNumber(addr);
    const n = toNumber(count);
    if (!Number.isSafeInteger(a) || !Number.isSafeInteger(n) || a < 0 || n < 0 || a > this.memorySize || n > this.memorySize - a) return this.diag(`memory range out of bounds: ${a}+${n}`, "UXB_MEMORY_RANGE");
    return {ok: true, address: a, count: n};
  },

  memoryLoad(mode, addr, width) {
    const modeResult = this.resolveMemoryMode(mode); if (modeResult && modeResult.ok === false) return modeResult;
    const r = this.memoryRange(addr, Number(width)); if (!r.ok) return r;
    if (Number(width) === 1) return this.readByte(r.address);
    if (Number(width) === 2) return this.readWord(r.address);
    if (Number(width) === 4) return this.readDWord(r.address);
    return this.diag(`unsupported memory load width: ${width}`, "UXB_MEMORY_WIDTH");
  },

  memoryStore(mode, addr, value, width) {
    const modeResult = this.resolveMemoryMode(mode); if (modeResult && modeResult.ok === false) return modeResult;
    const r = this.memoryRange(addr, Number(width)); if (!r.ok) return r;
    if (Number(width) === 1) return this.writeByte(r.address, value);
    if (Number(width) === 2) return this.writeWord(r.address, value);
    if (Number(width) === 4) return this.writeDWord(r.address, value);
    return this.diag(`unsupported memory store width: ${width}`, "UXB_MEMORY_WIDTH");
  },

  memoryCopyMode(mode, src, dst, count, width) {
    const modeResult = this.resolveMemoryMode(mode); if (modeResult && modeResult.ok === false) return modeResult;
    const bytes = toNumber(count) * toNumber(width);
    const rs = this.memoryRange(src, bytes); const rd = this.memoryRange(dst, bytes); if (!rs.ok) return rs; if (!rd.ok) return rd;
    const temp = new Uint8Array(bytes);
    for (let i = 0; i < bytes; i++) temp[i] = this.readByte(rs.address + i);
    for (let i = 0; i < bytes; i++) this.writeByte(rd.address + i, temp[i]);
    return 1;
  },

  memoryFillMode(mode, dst, value, count, width) {
    const modeResult = this.resolveMemoryMode(mode); if (modeResult && modeResult.ok === false) return modeResult;
    const n = toNumber(count); const w = toNumber(width); const r = this.memoryRange(dst, n * w); if (!r.ok) return r;
    for (let i = 0; i < n; i++) { const at = r.address + i * w; if (w === 1) this.writeByte(at, value); else if (w === 2) this.writeWord(at, value); else if (w === 4) this.writeDWord(at, value); else return this.diag(`unsupported memory fill width: ${width}`, "UXB_MEMORY_WIDTH"); }
    return 1;
  },

  memoryReadSequence(mode, addr, length) {
    const modeResult = this.resolveMemoryMode(mode); if (modeResult && modeResult.ok === false) return modeResult;
    const n = toNumber(length); const r = this.memoryRange(addr, n); if (!r.ok) return r;
    let out = ""; for (let i = 0; i < n; i++) out += String.fromCharCode(this.readByte(r.address + i)); return out;
  },

  memoryWriteSequence(mode, dst, source, length) {
    const modeResult = this.resolveMemoryMode(mode); if (modeResult && modeResult.ok === false) return modeResult;
    const text = String(source ?? ""); const n = toNumber(length); if (!Number.isSafeInteger(n) || n < 0 || n > text.length) return this.diag("sequence length exceeds source string length", "UXB_MEMORY_SEQUENCE_LENGTH");
    const r = this.memoryRange(dst, n); if (!r.ok) return r; for (let i = 0; i < n; i++) this.writeByte(r.address + i, text.charCodeAt(i) & 255); return 1;
  },

  writeByte(addr, value) {
    const a = Math.max(0, toNumber(addr) | 0);
    const v = toNumber(value) & 0xff;
    this.memoryBytes.set(a, v);
    return v;
  },

  readByte(addr) {
    const a = Math.max(0, toNumber(addr) | 0);
    return this.memoryBytes.get(a) ?? 0;
  },

  writeWord(addr, value) {
    const v = toNumber(value) & 0xffff;
    this.writeByte(addr, v & 0xff);
    this.writeByte(toNumber(addr) + 1, (v >>> 8) & 0xff);
    return v;
  },

  readWord(addr) {
    const b0 = this.readByte(addr);
    const b1 = this.readByte(toNumber(addr) + 1);
    return ((b1 << 8) | b0) & 0xffff;
  },

  writeDWord(addr, value) {
    const v = toNumber(value) >>> 0;
    this.writeByte(addr, v & 0xff);
    this.writeByte(toNumber(addr) + 1, (v >>> 8) & 0xff);
    this.writeByte(toNumber(addr) + 2, (v >>> 16) & 0xff);
    this.writeByte(toNumber(addr) + 3, (v >>> 24) & 0xff);
    return v;
  },

  readDWord(addr) {
    const b0 = this.readByte(addr);
    const b1 = this.readByte(toNumber(addr) + 1);
    const b2 = this.readByte(toNumber(addr) + 2);
    const b3 = this.readByte(toNumber(addr) + 3);
    return (((b3 << 24) >>> 0) | (b2 << 16) | (b1 << 8) | b0) >>> 0;
  },

  memFill(addr, value, count, unitBytes) {
    const base = toNumber(addr) | 0;
    const n = Math.max(0, toNumber(count) | 0);
    for (let i = 0; i < n; i++) {
      const at = base + i * unitBytes;
      if (unitBytes === 1) this.writeByte(at, value);
      else if (unitBytes === 2) this.writeWord(at, value);
      else this.writeDWord(at, value);
    }
    return n;
  },

  memCopy(dst, src, count, unitBytes) {
    const d = toNumber(dst) | 0;
    const s = toNumber(src) | 0;
    const n = Math.max(0, toNumber(count) | 0);
    for (let i = 0; i < n; i++) {
      const di = d + i * unitBytes;
      const si = s + i * unitBytes;
      if (unitBytes === 1) this.writeByte(di, this.readByte(si));
      else if (unitBytes === 2) this.writeWord(di, this.readWord(si));
      else this.writeDWord(di, this.readDWord(si));
    }
    return n;
  },

  callBuiltin(name, args = []) {
    const n = this.normalizeHostName(name);
    const execName = n.startsWith("EXEC") ? n.slice(4) : n;

    switch (execName) {
      case "LIST_NEW":
      case "LIST": return this.collectionNew("LIST");
      case "DICT_NEW":
      case "DICT": return this.collectionNew("DICT");
      case "SET_NEW":
      case "SET": return this.collectionNew("SET");

      case "LISTADD": return this.collectionOp("ADD", args[0], args[1]);
      case "LISTGET": return this.collectionOp("GET", args[0], args[1]);
      case "LISTSET": return this.collectionOp("SET", args[0], args[1], args[2]);
      case "LISTREMOVE": return this.collectionOp("REMOVE", args[0], args[1]);
      case "LISTCLEAR": return this.collectionOp("CLEAR", args[0]);
      case "LISTLEN": return this.collectionOp("LEN", args[0]);

      case "DICTSET": return this.collectionOp("SET", args[0], args[1], args[2]);
      case "DICTGET": return this.collectionOp("GET", args[0], args[1]);
      case "DICTHAS": return this.collectionOp("HAS", args[0], args[1]);
      case "DICTCLEAR": return this.collectionOp("CLEAR", args[0]);
      case "DICTLEN": return this.collectionOp("LEN", args[0]);
      case "DICTFINDKEY": return this.collectionOp("FINDKEY", args[0], args[1]);

      case "SETADD": return this.collectionOp("ADD", args[0], args[1]);
      case "SETHAS": return this.collectionOp("HAS", args[0], args[1]);
      case "SETREMOVE": return this.collectionOp("REMOVE", args[0], args[1]);
      case "SETCLEAR": return this.collectionOp("CLEAR", args[0]);
      case "SETLEN": return this.collectionOp("LEN", args[0]);
      case "SETFIND": return this.collectionOp("FIND", args[0], args[1]);

      case "SETSTRINGSIZE": return this.setStringSize(args[0]);
      case "SETNEWOFFSET": return (toNumber(args[0]) | 0) + (toNumber(args[1]) | 0);

      case "GETVAR":
      case "GETVARVALUE": return this.getVarValue(args[0], 0);
      case "ENSUREVAR": {
        const k = String(args[0] ?? "");
        if (!k) return 0;
        if (this.getVarValue(k, undefined) === undefined) this.setVarValue(k, args[1] ?? 0);
        return this.getVarValue(k, 0);
      }

      case "EVALNODEASTEXT": return toStringValue(args[0] ?? "");
      case "EVALNODE": return args[0] ?? null;
    }

    if (n.startsWith("EXEC")) return 0;
    return undefined;
  },

  async fileOpen(handle, mode = "text") {
    // Browser cannot open arbitrary local paths without user gesture.
    this.files.set(String(handle), {mode, data: ""});
    return handle;
  },

  filePut(handle, data) {
    const h = String(handle);
    const f = this.files.get(h) ?? {mode: "text", data: ""};
    f.data += toStringValue(data);
    this.files.set(h, f);
    return f.data.length;
  },

  fileGet(handle) {
    return this.files.get(String(handle))?.data ?? "";
  },

  eof(handle) {
    return this.files.has(String(handle)) ? 0 : 1;
  },

  lof(handle) {
    return (this.files.get(String(handle))?.data ?? "").length;
  },

  async aiPrompt(text) {
    if (globalThis.ai?.languageModel) {
      const availability = await globalThis.ai.languageModel.availability();
      if (availability === "readily" || availability === "after-download") {
        const session = await globalThis.ai.languageModel.create({systemPrompt: this.aiConfig.systemPrompt});
        return await session.prompt(String(text));
      }
    }
    if (globalThis.uxLocalAiEndpoint) {
      const r = await fetch(globalThis.uxLocalAiEndpoint, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({prompt: String(text), system: this.aiConfig.systemPrompt})
      });
      const j = await r.json();
      return j.result ?? j.text ?? "";
    }
    return `[AI fallback] ${text}`;
  },

  async callFfi(kind, library, symbol, args = []) {
    // Browser cannot directly call Windows DLL/API. Use localhost bridge.
    if (!this.ffiEndpoint) return this.diag(`FFI bridge yok: ${kind} ${library}.${symbol}`, "UXB_FFI_BRIDGE_MISSING");
    const r = await fetch(this.ffiEndpoint, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({kind, library, symbol, args})
    });
    return await r.json();
  },

  async callHost(name, args = []) {
    const raw = upperName(name);
    const n = this.normalizeHostName(raw);

    switch (n) {
      case "PRINT": return this.print(args[0] ?? "");
      case "PRINTLN": return this.println();
      case "PRINT_SEP_COMMA": return this.printRaw(" ");
      case "PRINT_SEP_SPACE": return this.printRaw(" ");
      case "PRINT_SEP_SEMICOLON": return 0;
      case "INPUT": return this.input(args[0] ?? "");
      case "CLS": return this.cls();
      case "COLOR": return this.color(args[0], args[1]);
      case "LOCATE": return this.locate(args[0], args[1]);
      case "SCREEN": return this.screen(args[0], args[1]);
      case "LINE": return this.line(args[0], args[1], args[2], args[3]);
      case "RECT": return this.rect(args[0], args[1], args[2], args[3]);
      case "FILLRECT": return this.fillRect(args[0], args[1], args[2], args[3]);
      case "TEXT": return this.text(args[0], args[1], args[2]);
      case "CIRCLE": return this.circle(args[0], args[1], args[2]);
      case "LOADSPRITE": return this.loadSprite(args[0], args[1]);
      case "DRAWSPRITE": return this.drawSprite(args[0], args[1], args[2], args[3], args[4]);
      case "LOADSHEET": return this.loadSheet(args[0], args[1], args[2], args[3]);
      case "DRAWFRAME": return this.drawFrame(args[0], args[1], args[2], args[3], args[4], args[5]);
      case "FLIP": return this.flip();
      case "KEYDOWN": return this.keyDown(args[0]);
      case "MOUSEX": return this.mouseX();
      case "MOUSEY": return this.mouseY();
      case "MOUSEDOWN": return this.mouseDown(args[0]);
      case "AI": case "AI$": case "AI_PROMPT": return this.aiPrompt(args[0]);

      // S-624: TIMER = yerel gece yarisindan beri kesirli saniye (ux_runtime_core.js ile ayni tanim).
      case "TIMER": { const d = new Date(); return d.getHours() * 3600 + d.getMinutes() * 60 + d.getSeconds() + d.getMilliseconds() / 1000; }
      case "SETSTRINGSIZE": return this.setStringSize(args[0]);
      case "SETNEWOFFSET": return (toNumber(args[0]) | 0) + (toNumber(args[1]) | 0);

      case "VARPTR":
      case "LPTR":
      case "CODEPTR": return this.allocPointer(`${n}:${toStringValue(args[0] ?? "")}`);

      case "PEEKB": return this.readByte(args[0]);
      case "PEEKW": return this.readWord(args[0]);
      case "PEEKD": return this.readDWord(args[0]);
      case "POKEB": return this.writeByte(args[0], args[1]);
      case "POKEW": return this.writeWord(args[0], args[1]);
      case "POKED": return this.writeDWord(args[0], args[1]);

      case "MEMFILLB": return this.memFill(args[0], args[1], args[2], 1);
      case "MEMFILLW": return this.memFill(args[0], args[1], args[2], 2);
      case "MEMFILLD": return this.memFill(args[0], args[1], args[2], 4);
      case "MEMCOPYB": return this.memCopy(args[0], args[1], args[2], 1);
      case "MEMCOPYW": return this.memCopy(args[0], args[1], args[2], 2);
      case "MEMCOPYD": return this.memCopy(args[0], args[1], args[2], 4);

      case "SADD": {
        const a = args[0];
        const b = args[1];
        const an = Number(a);
        const bn = Number(b);
        if (!Number.isNaN(an) && !Number.isNaN(bn)) return an + bn;
        return toStringValue(a) + toStringValue(b);
      }

      case "MAX2": return Math.max(toNumber(args[0]), toNumber(args[1]));
      case "FAKTORIYEL": {
        const n0 = Math.max(0, toNumber(args[0]) | 0);
        let acc = 1;
        for (let i = 2; i <= n0; i++) acc *= i;
        return acc;
      }
      case "FIBONACCI": {
        const n0 = Math.max(0, toNumber(args[0]) | 0);
        let a = 0;
        let b = 1;
        for (let i = 0; i < n0; i++) {
          const t = a + b;
          a = b;
          b = t;
        }
        return a;
      }
      case "AUTH_PROBE": return 1;

      case "NEW": {
        const className = args[0] ?? "OBJECT";
        if (typeof this.newObject === "function") {
          const init = Object.create(null);
          for (let i = 1; i < args.length; i++) init[`$${i}`] = args[i];
          return this.newObject(className, init);
        }
        return this.allocPointer(`OBJ:${className}`);
      }

      case "API":
      case "DLL": {
        const library = args[0] ?? "";
        const symbol = args[1] ?? "";
        const callArgs = args.slice(3);
        return this.callFfi(n.toLowerCase(), library, symbol, callArgs);
      }
      case "CALL":
      case "CDECL":
      case "STDCALL": {
        const library = args[0] ?? "";
        const symbol = args[1] ?? "";
        const callArgs = args.slice(2);
        return this.callFfi("ffi", library, symbol, callArgs);
      }

      case "OPEN": return this.fileOpen(args[0], args[1]);
      case "CLOSE": return this.files.delete(String(args[0])) ? 1 : 0;
      case "PUT": return this.filePut(args[0], args[1]);
      case "GET": return this.fileGet(args[0]);
      case "EOF": return this.eof(args[0]);
      case "LOF": return this.lof(args[0]);
    }

    if (["ABS","INT","FIX","SGN","SQR","SIN","COS","TAN","ATN","EXP","LOG","RND","RANDOMIZE","VAL","CINT","CLNG","CDBL","CSNG"].includes(n)) {
      return this.math(n, ...args);
    }

    if (["LEN","ASC","CHR","STR","UCASE","LCASE","LTRIM","RTRIM","MID","SPACE","STRING"].includes(n)) {
      return this.string(n, ...args);
    }

    const builtinHandled = this.callBuiltin(n, args);
    if (builtinHandled !== undefined) return builtinHandled;

    const entry = this.registry[n] ?? this.registry[raw];
    if (entry) {
      const handler = String(entry.handler ?? "");
      const jsPolicy = String(entry.jsPolicy ?? "");

      if (handler === "ux.math") return this.math(n, ...args);
      if (handler === "ux.string") return this.string(n, ...args);
      if (handler === "ux.collections") {
        const v = this.callBuiltin(n, args);
        if (v !== undefined) return v;
      }
      if (handler === "ux.file") {
        if (n === "OPEN") return this.fileOpen(args[0], args[1]);
        if (n === "PUT") return this.filePut(args[0], args[1]);
        if (n === "GET") return this.fileGet(args[0]);
        if (n === "EOF") return this.eof(args[0]);
        if (n === "LOF") return this.lof(args[0]);
      }
      if (handler === "ux.ffi" || jsPolicy === "bridge_only") {
        return this.callFfi("bridge", args[0] ?? "", args[1] ?? "", args.slice(2));
      }
      if (handler === "ux.callBuiltin" || jsPolicy === "host_runtime_dispatch" || jsPolicy === "js_runtime_structure") {
        const v = this.callBuiltin(n, args);
        if (v !== undefined) return v;
        return 0;
      }
      if (jsPolicy.startsWith("diagnostic")) {
        return 0;
      }
      return this.diag(`Host handler henüz bağlanmadı: ${n} (${jsPolicy})`, "UXB_HOST_HANDLER_PENDING");
    }

    return this.diag(`Bilinmeyen/uygulanmayan uXBasic çağrısı: ${n}`, "UXB_UNKNOWN_CALL");
  }
};

window.addEventListener("keydown", e => ux.keys.add(e.key.toUpperCase()));
window.addEventListener("keyup", e => ux.keys.delete(e.key.toUpperCase()));

export { UxbDiagnostic, toNumber, toStringValue };
