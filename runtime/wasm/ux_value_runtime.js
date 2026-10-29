const advanceWasmCursor = value => {
  for (const ch of value) {
    if (ch === '\n') { printRow++; printColumn = 0; }
    else if (ch === '\r') printColumn = 0;
    else if (ch === '\t') printColumn += 8 - printColumn % 8;
    else if (ch === '\b') printColumn = Math.max(0, printColumn - 1);
    else if (ch.codePointAt(0) >= 32 && ch !== '\x7f') printColumn++;
  }
};

const formatWasmNumber = (value, digits) => {
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

// Included inside the generated WASM host closure. Values crossing the numeric
// ABI are JavaScript Numbers; i32 handles and keys are converted only at lookup.
const wasmMemory = () => {
  const memory = globalThis.uxbWasmInstance?.exports?.memory;
  if (!memory) throw new Error('UXB_WASM_MEMORY_UNBOUND');
  return memory;
};
const text = handle => {
  if (handle === 0) return '';
  const memory = wasmMemory();
  const h = handle >>> 0;
  if (h + 16 > memory.buffer.byteLength) throw new Error('UXB_WASM_STRING_DESCRIPTOR_BOUNDS');
  const descriptor = new DataView(memory.buffer, h, 16);
  const ptr = descriptor.getUint32(0, true);
  const length = descriptor.getUint32(4, true);
  if (ptr + length > memory.buffer.byteLength) throw new Error('UXB_WASM_STRING_DATA_BOUNDS');
  return new TextDecoder('utf-8', { fatal: true }).decode(new Uint8Array(memory.buffer, ptr, length));
};
const internText = value => {
  const bytes = new TextEncoder().encode(String(value));
  if (bytes.length === 0) return 0;
  const handle = globalThis.uxbWasmInstance.exports.__uxb_str_alloc(bytes.length);
  const memory = wasmMemory(); // allocation can grow memory and detach the old view
  const ptr = new DataView(memory.buffer, handle, 16).getUint32(0, true);
  new Uint8Array(memory.buffer, ptr, bytes.length).set(bytes);
  return handle;
};

// File services keep the canonical 1..255 channels and one-based positions.
// This is a host provider: bytes live in real Node files, strings stay in WASM
// linear memory. Browser hosts may supply the existing host_call16 contract.
const wasmFileFs = typeof require === 'function' && typeof process !== 'undefined' && process.versions?.node
  ? require('node:fs') : null;
const wasmFiles = new Map();
const wasmFilePrint = [];
const fileInteger = (value, label, minimum = 0) => {
  if (!Number.isSafeInteger(value) || value < minimum) throw new Error('UXB_WASM_FILE_ARGUMENT: ' + label);
  return value;
};
const fileChannel = value => {
  const channel = fileInteger(value, 'channel must be in 1..255', 1);
  if (channel > 255) throw new Error('UXB_WASM_FILE_CHANNEL_RANGE: ' + channel);
  return channel;
};
const fileState = channel => {
  channel = fileChannel(channel);
  const file = wasmFiles.get(channel);
  if (!file) throw new Error('UXB_WASM_FILE_NOT_OPEN: ' + channel);
  return file;
};
const fileCloseAll = () => {
  let failure;
  for (const [channel, file] of wasmFiles) {
    try { wasmFileFs.closeSync(file.fd); } catch (error) { failure ??= error; }
    wasmFiles.delete(channel);
  }
  wasmFilePrint.length = 0;
  if (failure) throw failure;
};
const fileWrite = (file, bytes) => {
  if (!file.writable) throw new Error('UXB_WASM_FILE_NOT_WRITABLE');
  let done = 0;
  while (done < bytes.length) {
    const count = wasmFileFs.writeSync(file.fd, bytes, done, bytes.length - done, file.position);
    if (count <= 0) throw new Error('UXB_WASM_FILE_SHORT_WRITE');
    done += count;
    file.position += count;
  }
  if (file.mode === 'APPEND') file.position = wasmFileFs.fstatSync(file.fd).size;
};
const filePosition = (file, position) => {
  position = fileInteger(position, 'position must be at least 1', 1);
  const offset = (position - 1) * (file.mode === 'RANDOM' ? file.recordLength : 1);
  fileInteger(offset, 'position overflow');
  return offset;
};
const wasmFileCall = (id, args) => {
  if (typeof globalThis.uxbHostCall16 === 'function') {
    const value = globalThis.uxbHostCall16(id, ...args);
    if (typeof value !== 'number' || Number.isNaN(value)) throw new Error('UXB_WASM_FILE_PROVIDER_RESULT');
    return value;
  }
  if (!wasmFileFs) throw new Error('UXB_WASM_FILE_PROVIDER_MISSING: file I/O requires a Node or browser host provider');
  const argc = args[8] | 0;
  try {
    if (id === 50) {
      const path = text(args[0]), rawMode = text(args[1]).toUpperCase();
      const mode = ({I:'INPUT', IN:'INPUT', O:'OUTPUT', A:'APPEND', B:'BINARY', R:'RANDOM', RAND:'RANDOM'})[rawMode] || rawMode;
      const channel = fileChannel(args[2]);
      if (wasmFiles.has(channel)) throw new Error('UXB_WASM_FILE_CHANNEL_IN_USE: ' + channel);
      const flags = {INPUT:'r', OUTPUT:'w', APPEND:'a', BINARY:'r+', RANDOM:'r+'}[mode];
      if (!flags) throw new Error('UXB_WASM_FILE_MODE: ' + mode);
      const recordLength = mode === 'RANDOM' ? (argc === 4 ? fileInteger(args[3], 'record length', 1) : 4) : 0;
      let fd;
      try { fd = wasmFileFs.openSync(path, flags); }
      catch (error) {
        if ((mode !== 'BINARY' && mode !== 'RANDOM') || error.code !== 'ENOENT') throw error;
        fd = wasmFileFs.openSync(path, 'w+');
      }
      try {
        const position = mode === 'APPEND' ? wasmFileFs.fstatSync(fd).size : 0;
        wasmFiles.set(channel, {fd, mode, position, recordLength,
          readable:mode !== 'OUTPUT' && mode !== 'APPEND', writable:mode !== 'INPUT'});
      } catch (error) { wasmFileFs.closeSync(fd); throw error; }
      return 1;
    }
    if (id === 51) {
      if (!argc) { fileCloseAll(); return 1; }
      const channel = fileChannel(args[0]), file = fileState(channel);
      wasmFileFs.closeSync(file.fd);
      wasmFiles.delete(channel);
      return 1;
    }
    if (id === 60) {
      const context = wasmFilePrint.pop();
      if (!context) throw new Error('UXB_WASM_FILE_PRINT_CONTEXT');
      const lineEnd = typeof process !== 'undefined' && process.platform === 'win32' ? '\r\n' : '\n';
      const tail = context.sep === ';' || context.sep === ',' ? '' : lineEnd;
      fileWrite(fileState(context.channel), new TextEncoder().encode(context.text + tail));
      return 1;
    }
    if (id === 59) {
      const context = wasmFilePrint[wasmFilePrint.length - 1];
      if (!context) throw new Error('UXB_WASM_FILE_PRINT_CONTEXT');
      const kind = args[9] | 0;
      context.text += kind === 1 ? text(args[0]) : kind === 2 ? formatWasmNumber(Math.fround(args[0]), 7) : fmtNum(args[0]);
      context.sep = text(args[1]);
      if (context.sep === ',') context.text += '\t';
      else if (context.sep === ' ') context.text += ' ';
      return 0;
    }
    const file = fileState(args[0]);
    if (id === 58) {
      if (!file.writable) throw new Error('UXB_WASM_FILE_NOT_WRITABLE');
      wasmFilePrint.push({channel:args[0], text:'', sep:''});
      return 0;
    }
    if (id === 55) return file.position >= wasmFileFs.fstatSync(file.fd).size ? -1 : 0;
    if (id === 56) return wasmFileFs.fstatSync(file.fd).size;
    if (id === 54) {
      if (argc === 2) {
        if (file.mode !== 'BINARY' && file.mode !== 'RANDOM') throw new Error('UXB_WASM_FILE_SEEK_MODE');
        file.position = filePosition(file, args[1]);
      }
      return file.mode === 'RANDOM' ? Math.floor(file.position / file.recordLength) + 1 : file.position + 1;
    }
    if (id === 57) {
      if (!file.readable) throw new Error('UXB_WASM_FILE_NOT_READABLE');
      const parts = [], buffer = Buffer.alloc(4096);
      for (;;) {
        const count = wasmFileFs.readSync(file.fd, buffer, 0, buffer.length, file.position);
        if (!count) break;
        const newline = buffer.subarray(0, count).indexOf(10);
        const length = newline < 0 ? count : newline;
        parts.push(Buffer.from(buffer.subarray(0, length)));
        file.position += length + (newline < 0 ? 0 : 1);
        if (newline >= 0) break;
      }
      let bytes = Buffer.concat(parts);
      if (bytes.length && bytes[bytes.length - 1] === 13) bytes = bytes.subarray(0, bytes.length - 1);
      return internText(new TextDecoder('utf-8', {fatal:true, ignoreBOM:true}).decode(bytes));
    }
    if (id === 52 || id === 53) {
      if (file.mode !== 'BINARY' && file.mode !== 'RANDOM') throw new Error('UXB_WASM_FILE_BINARY_MODE');
      const isGet = id === 52;
      if (isGet && !file.readable) throw new Error('UXB_WASM_FILE_NOT_READABLE');
      if (!isGet && !file.writable) throw new Error('UXB_WASM_FILE_NOT_WRITABLE');
      const hasPosition = argc >= (isGet ? 2 : 3);
      const hasWidth = argc === (isGet ? 3 : 4);
      const width = hasWidth ? args[2] : file.mode === 'RANDOM' ? file.recordLength : 4;
      if (![1,2,4].includes(width) || (file.mode === 'RANDOM' && width !== file.recordLength))
        throw new Error('UXB_WASM_FILE_TRANSFER_WIDTH: requires 1, 2 or 4 bytes and matching RANDOM length');
      if (hasPosition && args[1] >= 0) file.position = filePosition(file, args[1]);
      const buffer = Buffer.alloc(width);
      if (isGet) {
        const count = wasmFileFs.readSync(file.fd, buffer, 0, width, file.position);
        if (count !== width) throw new Error('UXB_WASM_FILE_READ_PAST_END');
        file.position += count;
        return width === 4 ? buffer.readInt32LE() : buffer.readUIntLE(0, width);
      }
      const value = args[argc - 1];
      if (!Number.isSafeInteger(value)) throw new Error('UXB_WASM_FILE_BINARY_INTEGER_REQUIRED');
      if (width === 4) buffer.writeInt32LE(value | 0);
      else buffer.writeUIntLE((value >>> 0) & (width === 1 ? 255 : 65535), 0, width);
      fileWrite(file, buffer);
      return width;
    }
    throw new Error('UXB_WASM_FILE_OPERATION_UNBOUND: ' + id);
  } catch (error) {
    throw new Error('UXB_WASM_FILE_IO: ' + error.message, {cause:error});
  }
};
globalThis.uxbWasmCloseFiles = fileCloseAll;
const stringOp = (id, a, b) => {
  switch (id | 0) {
    case 1: return internText(text(a) + text(b));
    case 2: return text(a) === text(b) ? 0 : text(a) < text(b) ? -1 : 1;
    case 3: return text(a).length;
    case 4: return text(a).length ? text(a).charCodeAt(0) : 0;
    case 5: return internText(String.fromCharCode(a & 255));
    case 6: return internText(text(a).slice(0, Math.max(0, b | 0)));
    case 7: return internText(b > 0 ? text(a).slice(-b) : '');
    case 8: return internText(text(a).toUpperCase());
    case 9: return internText(text(a).toLowerCase());
    case 10: return internText(text(a).trim());
    case 11: return internText(text(a).replace(/^\s+/, ''));
    case 12: return internText(text(a).replace(/\s+$/, ''));
    case 99: throw new Error(text(a));
    default: throw new Error('UXB_WASM_STRING_OPERATION_UNBOUND:' + id);
  }
};
const hostNumber4 = (id, a, b, c, d) => {
  switch (id | 0) {
    case 1: write(a); return a;
    case 3: { const d = new Date(); return d.getHours() * 3600 + d.getMinutes() * 60 + d.getSeconds() + d.getMilliseconds() / 1000; } // S-624: TIMER = yerel gece yarisindan beri kesirli saniye
    case 4: return Math.random();
    case 10: return Math.abs(a);
    case 11: return Math.sqrt(a);
    case 12: return Math.sin(a);
    case 13: return Math.cos(a);
    case 14: return Math.tan(a);
    case 15: return Math.atan(a);
    case 16: return Math.log(a);
    case 17: return Math.exp(a);
    case 18: return Math.pow(a, b);
    case 19: return Math.trunc(a);
    case 20: return Math.floor(a);
    case 21: case 22: {
      const lower = Math.floor(a);
      const fraction = a - lower;
      return fraction < 0.5 ? lower : fraction > 0.5 ? lower + 1 : lower % 2 === 0 ? lower : lower + 1;
    }
    case 23: return Math.sign(a);
    case 24: return a;
    case 25: return Math.fround(a);
    case 33: { const value = Number.parseFloat(text(a)); return Number.isNaN(value) ? 0 : value; }
    case 34: return internText(fmtNum(a));
    case 35: return internText(formatWasmNumber(Math.fround(a), 7));
    case 86: case 87: {
      const array = arrays.get(a | 0);
      if (!array) throw new Error('UXB_WASM_ARRAY_MISSING:' + a);
      const index = (b | 0) - array.lower;
      if (index < 0 || index >= array.data.length) throw new Error('array index out of bounds');
      const code = c % 16, offset = Math.floor(c / 16);
      // STRING stores its stable linear-memory descriptor handle in an ABI-sized slot.
      const spec = {1:['Int8',1],2:['Uint8',1],3:['Int16',2],4:['Uint16',2],5:['Int32',4],6:['Uint32',4],9:['Float32',4],10:['Float64',8],11:['Uint32',8]}[code];
      if (!spec || offset < 0 || !Number.isSafeInteger(offset)) throw new Error('UXB_WASM_RECORD_FIELD_RANGE');
      let bytes = array.data[index];
      if (bytes !== 0 && !(bytes instanceof ArrayBuffer)) throw new Error('UXB_WASM_RECORD_ARRAY_TYPE');
      if (!bytes || bytes.byteLength < offset + spec[1]) {
        const grown = new ArrayBuffer(offset + spec[1]);
        if (bytes) new Uint8Array(grown).set(new Uint8Array(bytes));
        array.data[index] = bytes = grown;
      }
      const view = new DataView(bytes);
      if (id === 87) view['set' + spec[0]](offset, d, true);
      return view['get' + spec[0]](offset, true);
    }
    case 81: case 82: {
      const array = arrays.get(a | 0);
      if (!array) throw new Error('UXB_WASM_ARRAY_MISSING:' + a);
      const index = (b | 0) - array.lower;
      if (index < 0 || index >= array.data.length) throw new Error('array index out of bounds');
      if (id === 82) array.data[index] = c;
      return Number(array.data[index] ?? 0);
    }
    default: throw new Error('UXB_WASM_NUMERIC_OPERATION_UNBOUND:' + id);
  }
};
