#!/usr/bin/env node
import { cp, mkdir, readFile, rename, stat } from 'node:fs/promises';
import { homedir } from 'node:os';
import { basename, dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

// Installs the complete bundle, never just SKILL.md. No DSH settings/credentials
// are read or changed; an existing skill is retained as an explicit backup.
const source = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const args = process.argv.slice(2);
const homeIndex = args.indexOf('--home');
if (homeIndex >= 0 && (!args[homeIndex+1] || args[homeIndex+1].startsWith('--'))) throw new Error('--home requires a path');
const home = resolve(homeIndex >= 0 ? args[homeIndex+1] : process.env.DSH_HOME || join(homedir(),'.dsh'));
const name = 'blender-furniture-spaces';
const target = join(home,'skills',name);
let backup = null;
try {
  const exists = async path => { try { await stat(path); return true; } catch { return false; } };
  if (!await readFile(join(source,'SKILL.md'),'utf8').then(s=>s.includes('name: '+name))) throw new Error('Invalid source skill');
  if (target.toLowerCase() === source.toLowerCase()) {
    console.log(JSON.stringify({ok:true,alreadyAtTarget:true,directory:target},null,2));
  } else {
    if (await exists(target) && !args.includes('--update')) throw new Error('Skill already exists; use --update to retain a backup and replace it');
    await mkdir(dirname(target),{recursive:true});
    const staging = join(dirname(target),'.'+name+'-install-'+Date.now());
    await cp(source,staging,{recursive:true,filter:path=>!['__pycache__'].includes(basename(path))&&!path.endsWith('.pyc')});
    if (await exists(target)) {
      const backupRoot = join(home,'skill-backups');
      await mkdir(backupRoot,{recursive:true});
      backup=join(backupRoot,name+'-'+Date.now());
      await rename(target,backup);
    }
    try { await rename(staging,target); }
    catch (error) { if (backup) await rename(backup,target); throw error; }
    console.log(JSON.stringify({ok:true,directory:target,backup,invocation:'/blender-furniture-spaces'},null,2));
  }
} catch (error) {
  console.log(JSON.stringify({ok:false,error:error.message,backup},null,2));
  process.exitCode=1;
}
