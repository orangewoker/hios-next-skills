// Explicit integration audit against a task-owned live scene. Never clears a
// user's scene or reopens a file; the temporary probe property is removed.
import assert from 'node:assert/strict';
import { randomUUID } from 'node:crypto';
import { join } from 'node:path';
import { readFile } from 'node:fs/promises';
import { setTimeout as sleep } from 'node:timers/promises';
import { createClient, readSettings, selectSession } from '../skills/blender-furniture-spaces/scripts/blender.mjs';

const [pid, sceneName]=process.argv.slice(2);
if (!pid || !sceneName) throw new Error('Usage: node scripts/test-blender-live.mjs PID TASK_SCENE');
const session=await selectSession(pid),client=createClient(session);
const {workspace}=await readSettings();
const nonce=randomUUID();
const scene=JSON.stringify(sceneName),key=JSON.stringify('dsh-audit-'+nonce);
const script=`import bpy, threading\ns=bpy.data.scenes[${scene}]\nassert s.get('dsh_owned'), 'Audit only accepts a task-owned scene'\ns[${key}]=int(s.get(${key},0))+1\n_dsh_result={'mainThread':threading.current_thread() is threading.main_thread(),'count':s[${key}]}\n`;
const input={code:script,filename:'<live-probe>',searchPaths:[]};
try {
  assert.equal((await fetch(session.url+'/health')).status,403);
  assert.equal((await fetch(session.url+'/health',{headers:{Authorization:'Bearer '+session.token,Origin:'http://example.invalid'}})).status,403);
  const first=await client.submit('execute',input,nonce);
  const duplicate=await client.submit('execute',input,nonce);
  assert.equal(first.result.value.mainThread,true);
  assert.equal(first.result.value.count,1);
  assert.equal(duplicate.result.value.count,1);
  await assert.rejects(client.submit('execute',{...input,code:script+'# different'},nonce),/409/);
  const before=(await client.submit('inspect',{scene:sceneName})).result;
  const checkpoint=join(workspace,'tests',nonce+'.blend');
  const saved=await client.submit('checkpoint',{output:checkpoint});
  assert.equal(saved.result.activeFilePath,before.filePath);
  const bytes=await readFile(checkpoint);
  assert.ok(bytes.length>4096);
  // Blender can save uncompressed, legacy gzip, or current Zstandard files.
  assert.ok(bytes.subarray(0,7).equals(Buffer.from('BLENDER'))
    || bytes.subarray(0,4).toString('hex')==='28b52ffd'
    || bytes.subarray(0,2).toString('hex')==='1f8b');
  await assert.rejects(client.submit('save',{output:checkpoint}),/overwrite/);
  await assert.rejects(client.submit('save',{output:join(workspace,'..','outside-audit.blend')}),/inside/);
  const timeoutId=randomUUID();
  await assert.rejects(client.submit('execute',{code:'import time\ntime.sleep(.8)\n_dsh_result={"once":True}',searchPaths:[]},timeoutId,.1),
    error=>error.jobId===timeoutId && /still be running/.test(error.message));
  await sleep(1000);
  assert.equal((await client.job(timeoutId)).state,'done');
  assert.ok(before.modelBounds.size[0]>2.8 && before.modelBounds.size[0]<2.9);
  assert.ok(before.materials.every(m=>m.surfaceConnected));
  console.log(JSON.stringify({ok:true,pid:Number(pid),scene:sceneName,mainThread:true,
    duplicateExecutedOnce:true,conflictRejected:true,originRejected:true,unauthenticatedRejected:true,
    outputEscapeRejected:true,overwriteRejected:true,checkpointPreservesActiveFile:true,
    timeoutRecoveredWithoutReplay:true,modelBounds:before.modelBounds.size},null,2));
} finally {
  await client.submit('execute',{code:`import bpy\ns=bpy.data.scenes[${scene}]\nif ${key} in s: del s[${key}]\n`,searchPaths:[]});
}
