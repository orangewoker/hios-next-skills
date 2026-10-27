// Validate against the actually installed upstream DSH skill provider, without
// starting a model session or reading provider credentials.
import assert from 'node:assert/strict';
import { readFile, mkdtemp, rm } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { tmpdir } from 'node:os';
import { pathToFileURL } from 'node:url';

const home=resolve(process.argv[2] || process.env.DSH_HOME || '');
const installation=resolve(process.argv[3] || '');
if (!process.argv[2] || !process.argv[3]) throw new Error('Usage: node scripts/test-blender-dsh-discovery.mjs DSH_HOME DSH_INSTALL_DIRECTORY');
const file=join(installation,'node_modules/@deepseek-ai/dsh-skill-filesystem/lib/index.js');
const { FileSystemSkillProvider }=await import(pathToFileURL(file).href);
const warnings=[];
const ctx={get(){return undefined;},logger:{warn(message){warnings.push(message);}}};
const controller=new AbortController();
const emptyAgents=await mkdtemp(join(tmpdir(),'dsh-blender-provider-'));
const provider=new FileSystemSkillProvider(ctx,{signal:controller.signal,invalidate(){}},
  {dshHome:home,agentsHome:emptyAgents,watch:false});
try {
  const result=await provider.list({});
  const candidates=Array.isArray(result)?result:result.candidates;
  const candidate=candidates.find(s=>s.name==='blender-furniture-spaces');
  assert.ok(candidate,'Actual DSH provider did not discover installed skill');
  const skill=await provider.get(candidate,{signal:controller.signal});
  assert.equal(skill.resourceBase.kind,'directory');
  assert.ok(skill.content.includes('scripts/blender.mjs'));
  assert.ok(skill.invocation.modelInvocable && skill.invocation.userInvocable);
  const root=skill.resourceBase.path;
  for (const relative of ['addon/dsh_blender_bridge.py','lib/furniture_kit.py','examples/reference-sofa.py','references/furniture.md']) {
    assert.ok((await readFile(join(root,relative))).length>100,relative+' missing');
  }
  console.log(JSON.stringify({ok:true,name:skill.name,source:skill.source,resourceBase:root,
    modelInvocable:skill.invocation.modelInvocable,userInvocable:skill.invocation.userInvocable,
    warnings},null,2));
} finally {
  controller.abort();await provider.dispose();await rm(emptyAgents,{recursive:true,force:true});
}
