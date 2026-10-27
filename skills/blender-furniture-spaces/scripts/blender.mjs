#!/usr/bin/env node
import { execFile } from 'node:child_process';
import { createHash, randomUUID } from 'node:crypto';
import { copyFile, mkdir, readdir, readFile, writeFile, realpath, access } from 'node:fs/promises';
import { homedir } from 'node:os';
import { dirname, isAbsolute, join, relative, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { promisify } from 'node:util';
import { setTimeout as sleep } from 'node:timers/promises';

const execFileAsync = promisify(execFile);
export const skillRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
export const configHome = resolve(process.env.DSH_BLENDER_HOME || join(homedir(), '.dsh-blender'));
const settingsPath = join(configHome, 'settings.json');

export function parseArgs(argv) {
  const options = { command: argv[0] || 'doctor' };
  for (let i = 1; i < argv.length; i++) {
    if (!argv[i].startsWith('--')) throw new Error('Unexpected argument: ' + argv[i]);
    const key = argv[i].slice(2);
    if (['no-checkpoint', 'enable-via-blenderhub'].includes(key)) options[key] = true;
    else {
      if (!argv[i + 1] || argv[i + 1].startsWith('--')) throw new Error('Missing value: --' + key);
      options[key] = argv[++i];
    }
  }
  return options;
}

async function exists(path) { try { await access(path); return true; } catch { return false; } }
export async function readSettings() {
  if (await exists(settingsPath)) return JSON.parse(await readFile(settingsPath, 'utf8'));
  return { workspace: join(homedir(), 'Documents', 'DSH-Blender') };
}

export function inside(root, target) {
  const rel = relative(resolve(root), resolve(target));
  return !!rel && !isAbsolute(rel) && rel !== '..' && !rel.startsWith('..\\') && !rel.startsWith('../');
}

export async function safeOutput(root, target) {
  if (!isAbsolute(target)) throw new Error('Output must be absolute');
  root = resolve(root); target = resolve(target);
  if (!inside(root, target)) throw new Error('Output must be inside workspace: ' + root);
  // Resolve the nearest existing ancestor, so a symlink/junction cannot bypass the check.
  await mkdir(root, { recursive: true });
  const realRoot = await realpath(root);
  let parent = dirname(target);
  while (!await exists(parent)) parent = dirname(parent);
  const realParent = await realpath(parent);
  if (realParent !== realRoot && !inside(realRoot, realParent)) throw new Error('Output crosses workspace link');
  if (await exists(target)) throw new Error('Refusing to overwrite: ' + target);
  return target;
}

async function jsonFetch(url, options = {}, timeout = 5000) {
  const response = await fetch(url, { ...options, signal: AbortSignal.timeout(timeout), redirect: 'error' });
  const value = await response.json();
  if (!response.ok) throw new Error(`Bridge HTTP ${response.status}: ${value.error || 'request failed'}`);
  return value;
}

export function createClient(session) {
  const url = new URL(session.url);
  if (url.protocol !== 'http:' || url.hostname !== '127.0.0.1' || url.username || url.password || url.pathname !== '/') {
    throw new Error('Bridge must be a loopback HTTP endpoint');
  }
  const headers = { Authorization: 'Bearer ' + session.token, 'Content-Type': 'application/json' };
  const get = (path) => jsonFetch(session.url + path, { headers });
  return {
    health: () => get('/health'),
    job: (id) => get('/jobs/' + encodeURIComponent(id)),
    async submit(op, args, id = randomUUID(), timeoutSeconds = 180) {
      if (!/^[a-zA-Z0-9_-]{1,80}$/.test(id)) throw new Error('Invalid request ID (1–80 ASCII letters/digits/hyphens/underscores)');
      if (!Number.isFinite(timeoutSeconds) || timeoutSeconds < 0.1 || timeoutSeconds > 3600) throw new Error('Timeout must be 0.1–3600 seconds');
      let job;
      try {
        job = await jsonFetch(session.url + '/jobs', {
          method: 'POST', headers, body: JSON.stringify({ op, args, id }),
        });
      } catch (error) {
        error.jobId = id;
        error.message += '; submission may be uncertain, query this job ID before any replay';
        throw error;
      }
      const end = Date.now() + timeoutSeconds * 1000;
      while (!['done', 'failed'].includes(job.state)) {
        if (Date.now() >= end) {
          const error = new Error('Wait timed out; job may still be running. Use job --id ' + id);
          error.jobId = id; throw error;
        }
        await sleep(200);
        try { job = await get('/jobs/' + encodeURIComponent(id)); }
        catch (error) { error.jobId = id; throw error; }
      }
      if (job.state === 'failed') {
        const error = new Error(job.error || 'Blender job failed');
        error.jobId = id; error.traceback = job.traceback; throw error;
      }
      return { ok: true, jobId: id, state: job.state, result: job.result };
    },
  };
}

export async function sessions() {
  const directory = join(configHome, 'sessions');
  if (!await exists(directory)) return [];
  const live = [];
  for (const file of await readdir(directory)) {
    if (!/^bridge-\d+\.json$/.test(file)) continue;
    try {
      const session = JSON.parse(await readFile(join(directory, file), 'utf8'));
      const health = await createClient(session).health();
      if (health.pid === session.pid && health.protocol === 1) live.push(session);
    } catch { /* Stale session files do not establish a live connection. */ }
  }
  return live;
}

export async function runningBlenders({ run = execFileAsync, platform = process.platform, env = process.env } = {}) {
  if (platform !== 'win32') return [];
  const legacy = join(env.SystemRoot || env.WINDIR || 'C:\\Windows', 'System32', 'WindowsPowerShell', 'v1.0', 'powershell.exe');
  const script = "$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false); "
    + "@(Get-CimInstance Win32_Process -Filter \"Name='blender.exe'\" | Select-Object ProcessId,ExecutablePath) | ConvertTo-Json -Compress";
  for (const shell of ['pwsh', legacy]) {
    try {
      const { stdout } = await run(shell, ['-NoProfile', '-NonInteractive', '-Command', script],
        { windowsHide: true, timeout: 15000, encoding: 'utf8' });
      const result = JSON.parse(stdout.trim() || '[]');
      return (Array.isArray(result) ? result : [result]).map(p => ({ pid: p.ProcessId, binary: p.ExecutablePath }));
    } catch { /* PowerShell 7 is optional; fall back to Windows' bundled shell. */ }
  }
  return [];
}

export async function selectSession(pid) {
  const live = await sessions();
  const matches = pid ? live.filter(s => s.pid === Number(pid)) : live;
  if (!matches.length) throw new Error('No live Blender bridge. Run doctor and follow references/connection.md');
  if (matches.length !== 1) throw new Error('Multiple live Blenders; select --pid from doctor');
  return matches[0];
}

export async function install(options) {
  const settings = await readSettings();
  const running = await runningBlenders();
  const matching = options.pid ? running.filter(p => p.pid === Number(options.pid)) : running;
  const binary = options.blender || process.env.DSH_BLENDER_EXECUTABLE || process.env.HIOS_BLENDER_EXECUTABLE
    || (matching.length === 1 ? matching[0].binary : null) || settings.blender;
  if (!binary || !await exists(binary)) throw new Error('Specify the actual executable with --blender');
  const { stdout } = await execFileAsync(binary, ['--version'], { windowsHide: true, timeout: 15000 });
  const version = stdout.match(/Blender\s+(\d+)\.(\d+)/);
  if (!version) throw new Error('Unable to detect Blender version');
  const workspace = resolve(options.workspace || settings.workspace);
  let addons;
  if (process.platform === 'win32') addons = join(process.env.APPDATA, 'Blender Foundation', 'Blender', `${version[1]}.${version[2]}`, 'scripts', 'addons');
  else if (process.platform === 'darwin') addons = join(homedir(), 'Library', 'Application Support', 'Blender', `${version[1]}.${version[2]}`, 'scripts', 'addons');
  else addons = join(process.env.XDG_CONFIG_HOME || join(homedir(), '.config'), 'blender', `${version[1]}.${version[2]}`, 'scripts', 'addons');
  await mkdir(addons, { recursive: true });
  await mkdir(configHome, { recursive: true });
  await mkdir(workspace, { recursive: true });
  const source = join(skillRoot, 'addon', 'dsh_blender_bridge.py');
  const target = join(addons, 'dsh_blender_bridge.py');
  const data = await readFile(source);
  let backup = null;
  if (await exists(target) && !(await readFile(target)).equals(data)) {
    backup = target + '.' + Date.now() + '.bak'; await copyFile(target, backup);
  }
  await writeFile(target, data);
  await writeFile(settingsPath, JSON.stringify({ ...settings, workspace, blender: binary }, null, 2));
  let enabled = false;
  if (options['enable-via-blenderhub']) {
    if (!options.pid) throw new Error('--enable-via-blenderhub requires the intended --pid');
    const ping = await jsonFetch('http://127.0.0.1:8877/ping');
    if (ping.pid !== Number(options.pid)) throw new Error('BlenderHub PID does not match selected Blender');
    const value = await jsonFetch('http://127.0.0.1:8877/toggle', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ module: 'dsh_blender_bridge', enable: true }),
    }, 30000);
    if (!value.success || !value.enabled) throw new Error('BlenderHub did not enable addon: ' + JSON.stringify(value));
    enabled = true;
  }
  return { ok: true, binary, version: `${version[1]}.${version[2]}`, workspace, addonPath: target, backup,
    enabled, restartRequiredForAlreadyLoadedUpdate: !!backup,
    enableCommand: "import bpy, addon_utils; addon_utils.modules_refresh(); bpy.ops.preferences.addon_enable(module='dsh_blender_bridge'); bpy.ops.wm.save_userpref()" };
}

export async function main(argv = process.argv.slice(2)) {
  const options = parseArgs(argv);
  const settings = await readSettings();
  if (options.command === 'doctor') {
    const live = await sessions();
    return { ok: true, connected: live.length > 0, workspace: settings.workspace, skillRoot,
      sessions: live.map(({ token, url, ...s }) => s), running: await runningBlenders(),
      instructions: live.length ? 'Use --pid when several sessions exist' : 'Run install, then enable DSH Local Modeling Bridge in Blender' };
  }
  if (options.command === 'install') return install(options);
  const session = await selectSession(options.pid);
  const client = createClient(session);
  const id = options['request-id'] || randomUUID();
  const submit = (op, args, requestId = id) => client.submit(op, args, requestId, Number(options.timeout || 180));
  if (options.command === 'inspect') return submit('inspect', options.scene ? { scene: options.scene } : {});
  if (options.command === 'job') {
    if (!options.id) throw new Error('job requires --id');
    return { ok: true, job: await client.job(options.id) };
  }
  if (options.command === 'checkpoint') {
    const label = String(options.label || 'checkpoint').replace(/[^a-zA-Z0-9_-]/g, '_').slice(0, 50);
    const output = await safeOutput(settings.workspace, join(settings.workspace, 'checkpoints', `${Date.now()}-${label}-${id.slice(0, 8)}.blend`));
    return submit('checkpoint', { output });
  }
  if (options.command === 'exec') {
    if (!options.file) throw new Error('exec requires --file');
    const filename = resolve(options.file);
    const code = (await readFile(filename, 'utf8')).replace(/^\uFEFF/, '');
    if (Buffer.byteLength(code) > 1800000) throw new Error('Script too large');
    let checkpoint = null;
    if (!options['no-checkpoint']) {
      const hash = createHash('sha256').update(id).digest('hex').slice(0, 24);
      const output = join(settings.workspace, 'checkpoints', `before-${hash}.blend`);
      // Existing file may be the result of this same deduplicated job; server still refuses overwrite on fresh execution.
      if (!inside(settings.workspace, output)) throw new Error('Invalid checkpoint path');
      checkpoint = await client.submit('checkpoint', { output }, 'checkpoint-' + hash, Number(options.timeout || 180));
    }
    try {
      const value = await submit('execute', { filename, code, searchPaths: [join(skillRoot, 'lib')] });
      return { ...value, checkpoint: checkpoint?.result.path || null };
    } catch (error) {
      error.checkpoint = checkpoint?.result.path || null;
      throw error;
    }
  }
  if (options.command === 'save' || options.command === 'render') {
    if (!options.output) throw new Error(options.command + ' requires --output');
    const output = await safeOutput(settings.workspace, options.output);
    if (options.command === 'save') return submit('save', { output });
    const args = { output, engine: options.engine || 'keep', width: Number(options.width || 1000), height: Number(options.height || 1000) };
    if (options.camera) args.camera = options.camera;
    if (options.scene) args.scene = options.scene;
    if (options.samples) args.samples = Number(options.samples);
    if (![args.width, args.height, ...(args.samples ? [args.samples] : [])].every(Number.isFinite)) throw new Error('Render dimensions/samples must be numbers');
    return submit('render', args);
  }
  throw new Error('Unknown command: ' + options.command);
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  try { console.log(JSON.stringify(await main(), null, 2)); }
  catch (error) {
    console.log(JSON.stringify({ ok: false, error: error.message, jobId: error.jobId, checkpoint: error.checkpoint, traceback: error.traceback }, null, 2));
    process.exitCode = 1;
  }
}
