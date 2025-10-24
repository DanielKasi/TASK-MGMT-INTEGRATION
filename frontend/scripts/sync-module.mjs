#!/usr/bin/env node

import { execSync } from 'child_process';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * Sync a module from a Git repository into the host app
 * 
 * Usage:
 *   node scripts/sync-module.mjs \
 *     --repo <git-url> \
 *     --tag <version-tag> \
 *     --name <module-name>
 */

async function syncModule({ repo, tag, name }) {
  console.log(`\n🔄 Syncing module: ${name}@${tag}\n`);

  const tempDir = `/tmp/module-sync-${name}-${Date.now()}`;
  const rootDir = path.join(__dirname, '..');
  const targetDir = path.join(rootDir, 'src/app', name);
  const modulesDir = path.join(rootDir, 'modules');

  try {
    // Step 1: Clone the module repo at specific tag
    console.log('📦 Cloning module repository...');
    execSync(`git clone --depth 1 --branch ${tag} ${repo} ${tempDir}`, {
      stdio: 'inherit',
    });

    // Step 2: Read and validate module.json
    console.log('✅ Validating module manifest...');
    const manifestPath = path.join(tempDir, 'module.json');
    const manifest = JSON.parse(await fs.readFile(manifestPath, 'utf-8'));

    // Basic validation
    if (manifest.name !== name) {
      throw new Error(`Module name mismatch: expected ${name}, got ${manifest.name}`);
    }

    // Step 3: Check platform compatibility
    console.log('🔍 Checking platform compatibility...');
    const hostPackage = JSON.parse(
      await fs.readFile(path.join(rootDir, 'package.json'), 'utf-8')
    );
    
    // Validate peer dependencies
    for (const [pkg, version] of Object.entries(manifest.peerDeps || {})) {
      const hostVersion = hostPackage.dependencies[pkg];
      if (!hostVersion) {
        console.warn(`⚠️  Warning: ${pkg} not found in host dependencies`);
      }
      // TODO: Add semver range checking
    }

    // Step 4: Copy module core
    console.log('📋 Copying module files...');
    const srcAppPath = path.join(tempDir, 'src/app');
    
    // Remove existing module if it exists
    try {
      await fs.rm(targetDir, { recursive: true, force: true });
    } catch (err) {
      // Ignore if doesn't exist
    }

    // Copy src/app/* to host
    await fs.mkdir(targetDir, { recursive: true });
    await copyDir(srcAppPath, targetDir);

    // Step 5: Copy module descriptor
    console.log('🔧 Copying module descriptor...');
    const descriptorSrc = path.join(
      tempDir,
      'src/platform-integration/module-descriptor.ts'
    );
    const descriptorDest = path.join(
      rootDir,
      'src/lib/modules',
      `${name}.ts`
    );
    
    await fs.mkdir(path.dirname(descriptorDest), { recursive: true });
    await fs.copyFile(descriptorSrc, descriptorDest);

    // Step 6: Update module metadata
    console.log('📝 Updating module metadata...');
    await fs.mkdir(modulesDir, { recursive: true });
    
    const metadata = {
      name: manifest.name,
      version: manifest.version,
      tag,
      syncedAt: new Date().toISOString(),
      routes: manifest.routes,
      mountPath: manifest.mountPath,
    };
    
    await fs.writeFile(
      path.join(modulesDir, `${name}.json`),
      JSON.stringify(metadata, null, 2)
    );

    // Step 7: Update lock file
    console.log('🔒 Updating modules.lock.json...');
    const lockPath = path.join(rootDir, 'modules.lock.json');
    let lock = {};
    
    try {
      lock = JSON.parse(await fs.readFile(lockPath, 'utf-8'));
    } catch (err) {
      // Create new lock if doesn't exist
    }
    
    lock[name] = {
      version: manifest.version,
      tag,
      repo,
      syncedAt: new Date().toISOString(),
      checksum: await getDirectoryChecksum(targetDir),
    };
    
    await fs.writeFile(lockPath, JSON.stringify(lock, null, 2));

    // Step 8: Generate registry (simplified for now)
    console.log('⚙️  Generating module registry...');
    await generateRegistry(rootDir);

    // Cleanup
    await fs.rm(tempDir, { recursive: true, force: true });

    console.log(`\n✨ Successfully synced ${name}@${tag}\n`);
  } catch (error) {
    console.error('\n❌ Sync failed:', error.message);
    
    // Cleanup on error
    try {
      await fs.rm(tempDir, { recursive: true, force: true });
    } catch (err) {
      // Ignore cleanup errors
    }
    
    process.exit(1);
  }
}

async function copyDir(src, dest) {
  await fs.mkdir(dest, { recursive: true });
  const entries = await fs.readdir(src, { withFileTypes: true });

  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);

    if (entry.isDirectory()) {
      await copyDir(srcPath, destPath);
    } else {
      await fs.copyFile(srcPath, destPath);
    }
  }
}

async function getDirectoryChecksum(dir) {
  // Simplified checksum - could use crypto hash
  const stats = await fs.stat(dir);
  return stats.mtime.getTime().toString();
}

async function generateRegistry(rootDir) {
  const modulesLibDir = path.join(rootDir, 'src/lib/modules');
  const registryPath = path.join(rootDir, 'src/lib/redux/registry.ts');
  const storeRegistryPath = path.join(rootDir, 'src/lib/redux/store-registry.ts');

  // Read all module descriptors
  const moduleFiles = await fs.readdir(modulesLibDir);
  const modules = moduleFiles
    .filter(f => f.endsWith('.ts') && f !== 'index.ts')
    .map(f => f.replace('.ts', ''));

  // Generate module registry
  const registryContent = `
// AUTO-GENERATED - DO NOT EDIT
// Generated at: ${new Date().toISOString()}

${modules.map(m => `import { moduleDescriptor as ${m} } from './${m}';`).join('\n')}

export const moduleDescriptors = [
${modules.map(m => `  ${m},`).join('\n')}
];
`.trim();

  await fs.writeFile(registryPath, registryContent);

  // Generate store registry for Redux composition
  const storeRegistryContent = `
// AUTO-GENERATED - DO NOT EDIT
// Generated at: ${new Date().toISOString()}

import { combineReducers } from '@reduxjs/toolkit';
import { all, fork } from 'redux-saga/effects';

${modules.map(m => `import { moduleDescriptor as ${m} } from './${m}';`).join('\n')}

// Combine all module slices with namespacing
export const moduleSlices = combineReducers({
${modules.map(m => `  ...${m}.slices,`).join('\n')}
});

// Combine all module sagas
export function* moduleSagas() {
  yield all([
${modules.map(m => `    ...${m}.sagas.map(saga => fork(saga)),`).join('\n')}
  ]);
}

// Generate RootState type for host
export type ModuleRootState = ReturnType<typeof moduleSlices>;

// Store composition helper
export function createModuleStore() {
  return {
    slices: moduleSlices,
    sagas: moduleSagas,
  };
}
`.trim();

  await fs.writeFile(storeRegistryPath, storeRegistryContent);
}

// Parse CLI arguments
const args = process.argv.slice(2);
const params = {};

for (let i = 0; i < args.length; i += 2) {
  const key = args[i].replace('--', '');
  params[key] = args[i + 1];
}

if (!params.repo || !params.tag || !params.name) {
  console.error('Usage: sync-module.mjs --repo <url> --tag <tag> --name <name>');
  process.exit(1);
}

syncModule(params);
