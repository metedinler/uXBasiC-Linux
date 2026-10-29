/* QuickJS provider for globalThis.uxb. Requires uxjs_install_native_host(). */
(function installUxBasicQuickJsProvider(globalObject) {
  "use strict";
  const uxb = globalObject.uxb;
  const nativeHost = globalObject.__uxbNative;
  if (!uxb || uxb.contractVersion !== 1) throw new Error("UXB_CORE_RUNTIME_MISSING");
  if (!nativeHost) throw new Error("UXB_QUICKJS_NATIVE_HOST_MISSING");

  // Generated program.js exports globalThis.uxbMain. QuickJS loads first, then invokes explicitly.
  uxb.autoRun = false;
  uxb.provider = Object.freeze({
    name: "quickjs",
    version: String(nativeHost.version()),
    apiVersion: Number(nativeHost.apiVersion()),
    capabilities: Object.freeze(["console", "time", "random", "jobs", "json"]),
  });

  uxb.console.setSink({
    write: text => nativeHost.print(String(text)),
    writeLine: text => nativeHost.println(String(text)),
  });

  uxb.time.now = () => Number(nativeHost.nowMs());
  // S-624: TIMER = yerel gece yarisindan beri kesirli saniye (ux_runtime_core.js ile ayni tanim).
  uxb.time.timer = () => { const d = new Date(Number(nativeHost.nowMs())); return d.getHours() * 3600 + d.getMinutes() * 60 + d.getSeconds() + d.getMilliseconds() / 1000; };
  uxb.random.u32 = () => Number(nativeHost.randomU32()) >>> 0;
  uxb.random.next = () => uxb.random.u32() / 4294967296;

  uxb.host.install(async (name, args) => {
    const envelopeText = nativeHost.hostCall(String(name), uxb.json.stringify(args || []));
    const envelope = uxb.json.parse(envelopeText);
    if (!envelope || envelope.ok !== true) {
      const error = new Error(envelope && envelope.error ? envelope.error.message : `QuickJS host call failed: ${name}`);
      error.code = envelope && envelope.error ? envelope.error.code : "UXB_QUICKJS_HOST_ERROR";
      throw error;
    }
    return envelope.value;
  });
})(globalThis);
