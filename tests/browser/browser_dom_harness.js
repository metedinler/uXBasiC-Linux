"use strict";

const path = require("node:path");

const calls = [];
const context2d = {
  clearRect(...args) { calls.push(["clearRect", ...args]); },
  fillRect(...args) { calls.push(["fillRect", ...args]); },
  fillText(...args) { calls.push(["fillText", ...args]); }
};
const canvas = {
  id: "ux-canvas",
  width: 0,
  height: 0,
  getContext(kind) {
    if (kind !== "2d") return null;
    return context2d;
  }
};

global.document = {
  body: { appendChild() {} },
  getElementById(id) { return id === "ux-canvas" ? canvas : null; },
  createElement(kind) {
    if (kind !== "canvas") throw new Error(`Unexpected DOM element: ${kind}`);
    return canvas;
  }
};

const generatedProgram = process.argv[2];
if (!generatedProgram) throw new Error("Generated browser program path is required");
require(path.resolve(generatedProgram));

setImmediate(() => {
  const hasRect = calls.some(call => call.join(",") === "fillRect,10,10,120,60");
  const hasText = calls.some(call => call.join(",") === "fillText,uXBasic Canvas,20,100");
  if (canvas.width !== 800 || canvas.height !== 600 || !hasRect || !hasText) {
    console.error(JSON.stringify({ canvas: [canvas.width, canvas.height], calls }));
    process.exitCode = 1;
    return;
  }
  console.log("PASS_BROWSER_CANVAS");
});
