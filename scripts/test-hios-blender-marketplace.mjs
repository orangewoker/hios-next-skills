// Uses HIOS' production catalog/store/bridge and the installed upstream DSH
// registry. No model session, model credentials, or paid API is used.
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { setTimeout as sleep } from 'node:timers/promises';

const args = process.argv.slice(2);
const options = {};
for (let i = 0; i < args.length; i += 2) {
  if (!args[i].startsWith('--') || !args[i + 1]) throw new Error('Expected --key value');
  options[args[i].slice(2)] = args[i + 1];
}
for (const key of ['hios-source', 'dsh-install', 'output', 'pid']) assert.ok(options[key], '--' + key + ' required');
assert.ok(['staged', 'remote'].includes(options.mode || 'staged'));
const remote = options.mode === 'remote';
const repository = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const main = resolve(options['hios-source']);
const output = resolve(options.output);
const userdata = join(output, 'userdata');
const sid = 'blender-furniture-spaces';
const localIndex = JSON.parse(await readFile(join(repository, 'skills-index.json'), 'utf8'));
const entry = localIndex.skills.find(e => e.id === sid);
assert.ok(entry, 'Build the first package before validation');
await mkdir(output, { recursive: true });
const mainRequire = createRequire(join(main, 'package.json'));
const { buildSync } = mainRequire('esbuild');
const modules = [['SkillStore', 'skill-store'], ['SkillCatalog, skillTree', 'skill-catalog'], ['startDshSkillBridge, dshInstalledSkillPlugin', 'dsh-skill-bridge']];
const code = buildSync({ stdin: { contents: modules.map(([names, file]) => `export {${names}} from ${JSON.stringify(join(main, 'electron/services', file + '.ts').replaceAll('\\', '/'))};`).join('\n'), resolveDir: main, loader: 'ts' }, bundle: true, platform: 'node', format: 'cjs', external: ['electron'], write: false }).outputFiles[0].text;
const mod = { exports: {} };
const requests = [];
const electron = { app: { isPackaged: false, getPath: () => userdata }, net: { fetch: async (url, init) => {
  requests.push(new URL(url).pathname);
  if (remote) return fetch(url, init);
  if (new URL(url).pathname.endsWith('/skills-index.json')) return new Response(JSON.stringify(localIndex));
  if (new URL(url).pathname.endsWith('/' + entry.package)) return new Response(await readFile(join(repository, entry.package)));
  throw new Error('Unexpected staged request: ' + url);
} } };
new Function('require', 'module', 'exports', code)(id => id === 'electron' ? electron : mainRequire(id), mod, mod.exports);
const { SkillStore, SkillCatalog, skillTree, startDshSkillBridge, dshInstalledSkillPlugin } = mod.exports;
const store = new SkillStore({ skillContributions: () => [] });
store.builtinRoot = () => join(output, 'builtin');
// Reproduce an old installer containing this retired builtin. It must not
// shadow the independent marketplace package, and is not deleted by scanning.
await mkdir(join(output, 'builtin', sid), { recursive: true });
await writeFile(join(output, 'builtin', sid, 'SKILL.md'), `---\nname: ${sid}\ndescription: Legacy installer copy\n---\nLegacy body\n`);
assert.equal(store.reload().length, 0);
const catalog = new SkillCatalog(store);
const bridge = await startDshSkillBridge(store);
const saved = { HIOS_SKILL_URL: process.env.HIOS_SKILL_URL, HIOS_SKILL_TOKEN: process.env.HIOS_SKILL_TOKEN };
Object.assign(process.env, { HIOS_SKILL_URL: bridge.url, HIOS_SKILL_TOKEN: bridge.token });
const runtimeRequire = createRequire(join(resolve(options['dsh-install']), 'package.json'));
const { Context } = await import(pathToFileURL(runtimeRequire.resolve('@deepseek-ai/cordis')).href);
const { SkillRegistry, renderSkillContent } = await import(pathToFileURL(runtimeRequire.resolve('@deepseek-ai/dsh-skill')).href);
const actualDshVersion = runtimeRequire('@deepseek-ai/dsh-skill/package.json').version;
const ctx = new Context();
const fibers = [];
const run = promisify(execFile);
try {
  fibers.push(await ctx.plugin(SkillRegistry));
  const plugin = await import('data:text/javascript;base64,' + Buffer.from(dshInstalledSkillPlugin()).toString('base64'));
  fibers.push(await ctx.plugin(plugin));
  assert.deepEqual(await ctx.skills.list(), []);
  assert.equal((await fetch(bridge.url + '/list')).status, 403);
  const refreshed = await catalog.refresh(true);
  const source = refreshed.sources.find(s => s.url.includes('orangewoker/hios-next-skills'));
  assert.ok(source && !source.error, source?.error || 'Default marketplace unavailable');
  const indexed = refreshed.entries.find(e => e.id === sid && e.sourceId === source.id);
  assert.ok(indexed, 'Skill missing from marketplace index');
  assert.equal(indexed.sha256, entry.sha256);
  await catalog.install(source.id, sid);
  const deadline = Date.now() + 6500;
  while (!(await ctx.skills.list()).some(s => s.name === sid) && Date.now() < deadline) await sleep(100);
  const loaded = await ctx.skills.get(sid);
  assert.ok(loaded, 'Actual DSH registry did not discover newly installed skill');
  assert.equal(loaded.provider, 'hios-installed');
  assert.equal(loaded.resourceBase.kind, 'directory');
  assert.ok(renderSkillContent(loaded).includes(loaded.resourceBase.path));
  const root = loaded.resourceBase.path;
  for (const path of ['scripts/blender.mjs', 'lib/furniture_kit.py', 'addon/dsh_blender_bridge.py', 'examples/reference-sofa.py', 'references/connection.md']) assert.ok((await readFile(join(root, path))).length > 100);
  const baseline = skillTree(root);
  const cli = join(root, 'scripts/blender.mjs');
  async function command(...params) {
    const { stdout } = await run(process.execPath, [cli, ...params], { timeout: 240000, windowsHide: true, maxBuffer: 4 * 1024 * 1024 });
    const value = JSON.parse(stdout);
    assert.equal(value.ok, true, JSON.stringify(value));
    return value;
  }
  const doctor = await command('doctor');
  const live = doctor.sessions.find(s => s.pid === Number(options.pid));
  assert.ok(live, 'Selected Blender bridge is not running');
  const installed = await command('install', '--blender', live.binary);
  const controller = await import(pathToFileURL(cli).href);
  if (installed.restartRequiredForAlreadyLoadedUpdate) {
    const session = await controller.selectSession(options.pid);
    // Reload only this skill's addon after its current response has completed.
    // Does not restart Blender, load a file, clear a scene, or alter preferences.
    const reload = "import bpy\ndef _dsh_reload_market_bridge():\n import importlib, dsh_blender_bridge\n dsh_blender_bridge.unregister()\n importlib.invalidate_caches()\n importlib.reload(dsh_blender_bridge)\n dsh_blender_bridge.register()\n return None\nbpy.app.timers.register(_dsh_reload_market_bridge, first_interval=1.5)\n_dsh_result={'reloadScheduled':True}\n";
    await controller.createClient(session).submit('execute', { code: reload, searchPaths: [] });
    await sleep(2500);
    assert.ok((await command('doctor')).sessions.some(s => s.pid === live.pid && s.startedAt > live.startedAt), 'Addon reload not observed');
  }
  const before = (await command('inspect', '--pid', options.pid)).result;
  const stamp = new Date().toISOString().replaceAll(/[^0-9]/g, '').slice(0, 17);
  const prefix = 'DSH-Market-' + stamp;
  const task = join(doctor.workspace, 'tasks', 'marketplace-' + (remote ? 'remote-' : 'staged-') + stamp);
  await mkdir(task, { recursive: true });
  const config = join(task, 'config.json');
  await writeFile(config, JSON.stringify({ prefix }));
  const builder = join(task, 'build.py');
  const literal = value => JSON.stringify(value);
  await writeFile(builder, `from pathlib import Path\nDSH_SOFA_CONFIG=${literal(config)}\np=Path(${literal(join(root, 'examples/reference-sofa.py'))})\nexec(compile(p.read_text(encoding='utf-8'),str(p),'exec'))\n`);
  const built = await command('exec', '--file', builder, '--pid', options.pid);
  assert.ok(built.checkpoint, 'Pre-model checkpoint missing');
  const result = built.result.value;
  assert.equal(result.scene, prefix);
  assert.equal(result.curvedParts.length, 3);
  const inspected = (await command('inspect', '--scene', prefix, '--pid', options.pid)).result;
  assert.ok(inspected.modelBounds.size[0] > 2.8 && inspected.modelBounds.size[0] < 2.9);
  assert.ok(inspected.materials.every(m => m.surfaceConnected));
  const preview = join(task, 'preview.png'), front = join(task, 'front.png'), blend = join(task, 'model.blend');
  await command('render', '--scene', prefix, '--camera', result.camera, '--output', preview, '--width', '768', '--height', '768', '--engine', 'eevee', '--pid', options.pid);
  await command('render', '--scene', prefix, '--camera', prefix + '-Camera-Front', '--output', front, '--width', '768', '--height', '576', '--engine', 'eevee', '--pid', options.pid);
  await command('save', '--output', blend, '--pid', options.pid);
  const verify = join(task, 'verify.py');
  await writeFile(verify, `import bpy, sys\nassert ${literal(before.scene)} in bpy.data.scenes\n_dsh_result={'originalScenePreserved':True,'activeFilePath':bpy.data.filepath,'kitSource':sys.modules['furniture_kit'].__file__}\n`);
  const verified = await command('exec', '--file', verify, '--pid', options.pid);
  assert.equal(verified.result.value.activeFilePath, before.filePath);
  assert.equal(resolve(verified.result.value.kitSource), resolve(root, 'lib/furniture_kit.py'));
  const preserved = (await command('inspect', '--scene', before.scene, '--pid', options.pid)).result;
  assert.deepEqual(preserved.objects, before.objects, 'Original scene objects changed');
  assert.equal(skillTree(root), baseline, 'Executing this installed skill changed its resource tree');
  await catalog.install(source.id, sid);
  assert.equal(skillTree(root), baseline, 'Clean reinstall failed or changed installed content');
  const report = { ok: true, mode: remote ? 'remote' : 'staged', id: sid, version: indexed.version,
    sha256: indexed.sha256, bytes: indexed.size, actualDshVersion, provider: loaded.provider,
    resourceBase: root, newlyInstalledSkillDiscovered: true, legacyBuiltinIgnored: true,
    installedTreeUnchangedAfterExecution: true, reinstallAfterExecutionPassed: true,
    pid: live.pid, scene: prefix, originalScenePreserved: true, checkpoint: built.checkpoint,
    curvedParts: result.curvedParts, modelBounds: inspected.modelBounds, task, preview, front, blend,
    modelSessionUsed: false, requests };
  await writeFile(join(output, 'report.json'), JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
} finally {
  bridge.close();
  for (const fiber of fibers.reverse()) await fiber.dispose();
  for (const [key, value] of Object.entries(saved)) { if (value === undefined) delete process.env[key]; else process.env[key] = value; }
}
