import test from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { mkdtemp, mkdir, writeFile, symlink, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { once } from 'node:events';
import { createClient, inside, parseArgs, safeOutput, runningBlenders } from '../skills/blender-furniture-spaces/scripts/blender.mjs';

test('Blender discovery falls back to bundled Windows PowerShell without requiring PowerShell 7', async () => {
  const calls = [];
  const result = await runningBlenders({ platform: 'win32', env: { SystemRoot: 'C:\\Windows' }, run: async (shell, args, options) => {
    calls.push(shell);
    assert.equal(options.windowsHide, true);
    assert.ok(args.includes('-NonInteractive'));
    if (shell === 'pwsh') throw Object.assign(new Error('not installed'), { code: 'ENOENT' });
    return { stdout: JSON.stringify({ ProcessId: 456, ExecutablePath: 'D:\\中文 路径\\blender.exe' }) };
  } });
  assert.equal(calls.length, 2);
  assert.ok(calls[1].endsWith('powershell.exe'));
  assert.deepEqual(result, [{ pid: 456, binary: 'D:\\中文 路径\\blender.exe' }]);
  assert.deepEqual(await runningBlenders({ platform: 'darwin', run: () => { throw new Error('unexpected shell'); } }), []);
});

test('CLI parses quoted paths and rejects missing values', () => {
  assert.deepEqual(parseArgs(['exec', '--file', 'C:\\中文 路径\\sofa.py', '--no-checkpoint']),
    { command: 'exec', file: 'C:\\中文 路径\\sofa.py', 'no-checkpoint': true });
  assert.throws(() => parseArgs(['render', '--output']), /Missing value/);
  assert.throws(() => parseArgs(['exec', 'script.py']), /Unexpected/);
});

test('output guard rejects siblings, traversal, relative paths, overwrites and junction escapes', async () => {
  const temp = await mkdtemp(join(tmpdir(), 'dsh-blender-path-'));
  try {
    const root = join(temp, 'workspace'), outside = join(temp, 'elsewhere');
    await mkdir(root); await mkdir(outside);
    assert.equal(inside(root, root), false);
    assert.equal(inside(root, root + '-sibling/file.png'), false);
    assert.equal(inside(root, join(root, '..', 'escape.png')), false);
    assert.equal(await safeOutput(root, join(root, 'new', 'a.png')), join(root, 'new', 'a.png'));
    await assert.rejects(safeOutput(root, 'relative.png'), /absolute/);
    await assert.rejects(safeOutput(root, join(outside, 'a.png')), /inside/);
    await writeFile(join(root, 'original.blend'), 'sentinel');
    await assert.rejects(safeOutput(root, join(root, 'original.blend')), /overwrite/);
    await symlink(outside, join(root, 'linked'), process.platform === 'win32' ? 'junction' : 'dir');
    await assert.rejects(safeOutput(root, join(root, 'linked', 'a.png')), /link/);
  } finally { await rm(temp, { recursive: true, force: true }); }
});

async function mockBridge(callback) {
  let posts = 0;
  const jobs = new Map();
  const server = createServer(async (req, res) => {
    assert.equal(req.headers.authorization, 'Bearer test-token');
    const send = (status, body) => { res.writeHead(status, { 'content-type': 'application/json' }); res.end(JSON.stringify(body)); };
    if (req.method === 'POST') {
      let body = ''; for await (const chunk of req) body += chunk;
      const data = JSON.parse(body); posts++;
      if (data.op === 'fail') { send(202, { state: 'failed', error: 'Python error', traceback: 'test trace' }); return; }
      if (data.op === 'never') { jobs.set(data.id, { state: 'running' }); send(202, { state: 'running' }); return; }
      const previous = jobs.get(data.id);
      if (previous && previous.code !== data.args.code) { send(409, { error: 'ID conflict' }); return; }
      const job = previous || { state: 'done', code: data.args.code, result: { value: 42 } };
      jobs.set(data.id, job); send(202, job); return;
    }
    if (req.url === '/health') { send(200, { pid: 123, protocol: 1 }); return; }
    send(200, jobs.get(req.url.slice('/jobs/'.length)) || { state: 'done', result: {} });
  });
  server.listen(0, '127.0.0.1'); await once(server, 'listening');
  const client = createClient({ url: `http://127.0.0.1:${server.address().port}`, token: 'test-token' });
  try { await callback(client, () => posts); }
  finally { server.closeAllConnections(); await new Promise(r => server.close(r)); }
}

test('client only accepts local endpoints', () => {
  assert.throws(() => createClient({ url: 'https://example.com', token: '' }), /loopback/);
  assert.throws(() => createClient({ url: 'http://localhost:8877', token: '' }), /loopback/);
  assert.throws(() => createClient({ url: 'http://x:y@127.0.0.1:8877', token: '' }), /loopback/);
});

test('request ID deduplication, conflicts and meaningful failure details', async () => {
  await mockBridge(async client => {
    assert.equal((await client.health()).pid, 123);
    assert.equal((await client.submit('execute', { code: 'one' }, 'same-id')).result.value, 42);
    assert.equal((await client.submit('execute', { code: 'one' }, 'same-id')).result.value, 42);
    await assert.rejects(client.submit('execute', { code: 'different' }, 'same-id'), /conflict/);
    await assert.rejects(client.submit('fail', {}, 'failed-id'), error => error.jobId === 'failed-id' && error.traceback === 'test trace');
    await assert.rejects(client.submit('execute', {}, '../invalid'), /Invalid request/);
  });
});

test('timeout returns recoverable job ID without replay', async () => {
  await mockBridge(async (client, posts) => {
    await assert.rejects(client.submit('never', {}, 'long-render', .1),
      error => error.jobId === 'long-render' && /still be running/.test(error.message));
    assert.equal(posts(), 1);
    assert.equal((await client.job('long-render')).state, 'running');
    assert.equal(posts(), 1);
  });
});
