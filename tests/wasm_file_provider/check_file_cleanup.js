// Observe real Node file descriptors; every intercepted operation still calls fs.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const [runner, expectedExit = '0'] = process.argv.slice(2);
if (!runner) throw new Error('usage: node check_file_cleanup.js runner.js [expected-program-exit]');
const open = fs.openSync, close = fs.closeSync;
const live = new Set();
let opened = 0, closed = 0;
fs.openSync = function(...args) {
  const fd = open.apply(this, args);
  if (typeof args[0] === 'string' && path.basename(args[0]).startsWith('cleanup_')) {
    live.add(fd); opened++;
  }
  return fd;
};
fs.closeSync = function(fd) {
  const result = close.call(this, fd);
  if (live.delete(fd)) closed++;
  return result;
};
process.once('beforeExit', () => {
  fs.openSync = open; fs.closeSync = close;
  try {
    assert.equal(process.exitCode || 0, Number(expectedExit), 'program must take its intended exit path');
    assert.ok(opened > 0, 'the program must open a real file');
    assert.equal(live.size, 0, 'runner must close all real descriptors before process exit');
    assert.equal(closed, opened);
    console.log(`PASS real file cleanup: opened=${opened} closed=${closed} program_exit=${expectedExit}`);
    process.exitCode = 0;
  } catch (error) { console.error(error); process.exitCode = 1; }
});
require(path.resolve(runner));
