/** Index active sources without modifying another agent's instructions/hooks.
 * GitNexus 1.4.5 has no FreeBASIC grammar. Supplement its native-language graph
 * with a deliberately conservative live-source FreeBASIC symbol/call index.
 * Calls are lexical candidates, not a compiler-resolved or runtime call graph.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { pathToFileURL, fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';

const repo = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const runtimeArg = process.argv.indexOf('--runtime');
if (runtimeArg < 0 || !process.argv[runtimeArg + 1]) throw new Error('Pass --runtime <installed GitNexus package directory>');
const runtime = path.resolve(process.argv[runtimeArg + 1]);
const api = async relative => import(pathToFileURL(path.join(runtime, 'dist', relative)).href);
const { getStoragePaths, saveMeta, registerRepo } = await api('storage/repo-manager.js');
const { storagePath, lbugPath } = getStoragePaths(repo);
if (process.argv.includes('--register-only')) {
  await registerRepo(repo, JSON.parse(await fs.readFile(path.join(storagePath, 'meta.json'), 'utf8')));
  console.log('Registered existing uxb index; no agent configuration changed.');
  process.exit(0);
}
try { await fs.stat(lbugPath); throw new Error('Index exists: preserve it before rebuilding; automatic deletion is disabled.'); }
catch (e) { if (e.code !== 'ENOENT') throw e; }
const { runPipelineFromRepo } = await api('core/ingestion/pipeline.js');
const { processStructure } = await api('core/ingestion/structure-processor.js');
const { processCommunities } = await api('core/ingestion/community-processor.js');
const { processProcesses } = await api('core/ingestion/process-processor.js');
const { generateId } = await api('lib/utils.js');
const { initLbug, loadGraphToLbug, getLbugStats, closeLbug, createFTSIndex } = await api('core/lbug/lbug-adapter.js');
let lastPhase = '';
const progress = p => { if (p.phase !== lastPhase) { lastPhase = p.phase; console.log(p.phase, p.message); } };
const result = await runPipelineFromRepo(repo, progress);
const graph = result.graph;
const packageInfo = JSON.parse(await fs.readFile(path.join(runtime, 'package.json'), 'utf8'));
const sources = [], symbols = [];
async function walk(dir) {
  for (const entry of await fs.readdir(path.join(repo, dir), { withFileTypes: true })) {
    const relative = `${dir}/${entry.name}`;
    if (entry.isSymbolicLink()) continue;
    if (entry.isDirectory() && !/^(?:_retired|backups|archive|vendor|third_party|build|bin)$/i.test(entry.name)) await walk(relative);
    else if (entry.isFile() && /\.(?:fbs|bas|bi)$/i.test(entry.name)) sources.push(relative);
  }
}
await walk('src'); await walk('compiler'); await walk('libsx');
processStructure(graph, sources);
const hashes = {};
// Remove strings and comments before identifying call candidates; no model text
// or historic line number is treated as a live source fact.
const codeOnly = line => line.replace(/"(?:""|[^"])*"/g, ' ').replace(/'.*$/, '').replace(/^\s*REM\b.*$/i, '');
for (const file of sources) {
  const content = await fs.readFile(path.join(repo, file), 'utf8');
  hashes[file] = crypto.createHash('sha256').update(content).digest('hex');
  const fileId = generateId('File', file);
  graph.addNode({ id: fileId, label: 'File', properties: { name: path.basename(file), filePath: file, content } });
  const lines = content.split(/\r?\n/);
  let current = null;
  for (let i = 0; i < lines.length; i++) {
    const code = codeOnly(lines[i]);
    const start = code.match(/^\s*(?:(?:PUBLIC|PRIVATE|STATIC|VIRTUAL|ABSTRACT|OVERRIDE)\s+)*(FUNCTION|SUB|CONSTRUCTOR|DESTRUCTOR|OPERATOR)\s+([^\s(]+)/i);
    if (start) {
      if (current) throw new Error(`Unclosed routine ${current.name} at ${file}:${i + 1}`);
      current = { name: start[2], kind: start[1].toUpperCase(), file, line: i, body: [] };
    }
    if (current) current.body.push(code);
    if (current && /^\s*END\s+(?:FUNCTION|SUB|CONSTRUCTOR|DESTRUCTOR|OPERATOR)\b/i.test(code)) {
      const symbol = { ...current, end: i, id: generateId('Function', `${file}:${current.name}:${current.line}`) };
      graph.addNode({ id: symbol.id, label: 'Function', properties: {
        name: symbol.name, filePath: file, startLine: symbol.line, endLine: i,
        content: lines.slice(symbol.line, i + 1).join('\n'), isExported: !/^\s*PRIVATE\b/i.test(lines[symbol.line])
      } });
      graph.addRelationship({ id: `${fileId}:defines:${symbol.id}`, type: 'DEFINES', sourceId: fileId, targetId: symbol.id, confidence: 1, reason: 'live FreeBASIC routine declaration' });
      symbols.push(symbol); current = null;
    }
    const include = lines[i].match(/^\s*#include\s+(?:once\s+)?"([^"]+)"/i);
    if (include) {
      const target = path.posix.normalize(path.posix.join(path.posix.dirname(file), include[1].replaceAll('\\', '/')));
      if (!target.startsWith('../') && sources.includes(target)) graph.addRelationship({ id: `${fileId}:include:${target}`, type: 'IMPORTS', sourceId: fileId, targetId: generateId('File', target), confidence: 1, reason: 'literal relative #include' });
    }
  }
  if (current) throw new Error(`Unclosed routine ${current.name} in ${file}`);
}
const byName = new Map();
for (const s of symbols) { const key = s.name.toUpperCase(); if (!byName.has(key)) byName.set(key, []); byName.get(key).push(s); }
let calls = 0;
for (const s of symbols) {
  const names = new Set();
  for (const line of s.body.slice(1, -1)) {
    for (const m of line.matchAll(/\b([A-Za-z_][\w.]*)\s*\(/g)) names.add(m[1].toUpperCase());
    const bare = line.match(/^\s*(?:CALL\s+)?([A-Za-z_][\w.]*)\s+(?!AS\b)/i);
    if (bare) names.add(bare[1].toUpperCase());
  }
  for (const name of names) {
    let targets = byName.get(name) ?? [];
    const local = targets.filter(t => t.file === s.file);
    if (local.length === 1) targets = local;
    for (const t of targets) {
      graph.addRelationship({ id: `${s.id}:calls:${t.id}`, type: 'CALLS', sourceId: s.id, targetId: t.id,
        confidence: targets.length === 1 ? 0.8 : 0.4,
        reason: targets.length === 1 ? 'FreeBASIC lexical call candidate; not type-resolved' : 'FreeBASIC ambiguous name candidate' });
      calls++;
    }
  }
}
for (const node of graph.nodes) if (node.label === 'Community' || node.label === 'Process') graph.removeNode(node.id);
console.log(`FreeBASIC live graph: ${sources.length} files, ${symbols.length} routines, ${calls} lexical candidate edges`);
const communities = await processCommunities(graph);
await processProcesses(graph, communities.memberships);
await fs.mkdir(storagePath, { recursive: true });
try {
  await initLbug(lbugPath);
  const loaded = await loadGraphToLbug(graph, repo, storagePath, message => console.log(message));
  for (const [label, name] of [['File', 'file_fts'], ['Function', 'function_fts'], ['Class', 'class_fts'], ['Method', 'method_fts'], ['Interface', 'interface_fts']]) await createFTSIndex(label, name, ['name', 'content']);
  const stats = await getLbugStats();
  let commit = '';
  try { commit = execFileSync('git', ['-c', `safe.directory=${repo.replaceAll('\\', '/')}`, '-C', repo, 'rev-parse', 'HEAD'], { encoding: 'utf8' }).trim(); }
  catch (e) { throw new Error(`Cannot read source commit: ${e.message}`); }
  const meta = { repoPath: repo, lastCommit: commit, indexedAt: new Date().toISOString(), stats: { files: graph.nodes.filter(n => n.label === 'File').length, ...stats, communities: graph.nodes.filter(n => n.label === 'Community').length, processes: graph.nodes.filter(n => n.label === 'Process').length, embeddings: 0 } };
  await saveMeta(storagePath, meta);
  const coverage = { gitnexusVersion: packageInfo.version, meta, freebasic: { files: sources.length, routines: symbols.length, lexicalCalls: calls, confidence: '0.8 unique / 0.4 ambiguous; no BYREF, macro or dynamic dispatch resolution' }, sourceHashes: hashes, warnings: loaded.warnings, modelCalls: 0, modifiesAgentConfig: false };
  await fs.writeFile(path.join(storagePath, 'uxb_coverage.json'), JSON.stringify(coverage, null, 2));
  console.log(JSON.stringify({ ...stats, freebasicFiles: sources.length, freebasicRoutines: symbols.length, database: lbugPath }));
} finally { await closeLbug(); }
// Registration is a separate authorized operation because it writes ~/.gitnexus.
