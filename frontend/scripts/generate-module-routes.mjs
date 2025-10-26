#!/usr/bin/env node

import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import readline from 'readline';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * Script to automatically generate module routes by scanning src/app for page.tsx files
 * 
 * Usage:
 *   node scripts/generate-module-routes.mjs
 */

// Create readline interface for user input
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

// Helper function to prompt user for input
function promptUser(question) {
  return new Promise((resolve) => {
    rl.question(question, resolve);
  });
}

// Helper function to validate mount path
function validateMountPath(mountPath) {
  // Remove leading slash if present
  const cleanPath = mountPath.startsWith('/') ? mountPath.slice(1) : mountPath;
  
  // Check for spaces
  if (cleanPath.includes(' ')) {
    throw new Error('Module name cannot contain spaces');
  }
  
  // Check for invalid characters (only allow lowercase letters, numbers, and hyphens)
  if (!/^[a-z0-9-]+$/.test(cleanPath)) {
    throw new Error('Module name can only contain lowercase letters, numbers, and hyphens');
  }
  
  // Ensure module name is not empty
  if (!cleanPath || cleanPath.length === 0) {
    throw new Error('Module name cannot be empty');
  }
  
  // Ensure it starts with a letter
  if (!/^[a-z]/.test(cleanPath)) {
    throw new Error('Module name must start with a letter');
  }
  
  // Auto-prepend 'apps/' to create the full mount path
  return `/apps/${cleanPath}`;
}

// Helper function to convert file path to route
function filePathToRoute(filePath, srcAppPath) {
  // Remove src/app prefix and page.tsx suffix
  let route = filePath
    .replace(srcAppPath, '')
    .replace(/\/page\.tsx$/, '')
    .replace(/\\/g, '/'); // Normalize path separators
  
  // Handle root route
  if (route === '') {
    route = '/';
  }
  
  // Handle dynamic routes (e.g., [id] -> [id])
  // Keep dynamic segments as-is since they're valid Next.js routes
  
  return route;
}

// Helper function to scan directory recursively for page.tsx files
async function findPageFiles(dir, srcAppPath) {
  const pageFiles = [];
  
  try {
    const entries = await fs.readdir(dir, { withFileTypes: true });
    
    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);
      
      if (entry.isDirectory()) {
        // Skip certain directories
        if (entry.name.startsWith('.') || entry.name === 'node_modules') {
          continue;
        }
        
        // Recursively scan subdirectories
        const subPageFiles = await findPageFiles(fullPath, srcAppPath);
        pageFiles.push(...subPageFiles);
      } else if (entry.name === 'page.tsx') {
        // Found a page.tsx file
        const route = filePathToRoute(fullPath, srcAppPath);
        pageFiles.push({
          filePath: fullPath,
          route: route
        });
      }
    }
  } catch (err) {
    console.warn(`Warning: Could not read directory ${dir}: ${err.message}`);
  }
  
  return pageFiles;
}

// Main function
async function generateModuleRoutes() {
  console.log('\n🔍 Module Route Generator\n');
  
  try {
    // Get mount path from user
    let mountPath;
    let isValidPath = false;
    
    while (!isValidPath) {
      const userInput = await promptUser('Enter the module name (e.g., "tasks", "accounting"): ');
      
      try {
        mountPath = validateMountPath(userInput.trim());
        isValidPath = true;
        console.log(`✅ Mount path: ${mountPath}`);
      } catch (error) {
        console.log(`❌ ${error.message}`);
        console.log('Please try again.\n');
      }
    }
    
    // Find src/app directory
    const rootDir = path.join(__dirname, '..');
    const srcAppPath = path.join(rootDir, 'src', 'app');
    
    console.log(`\n📁 Scanning ${srcAppPath} for page.tsx files...`);
    
    // Check if src/app exists
    try {
      await fs.access(srcAppPath);
    } catch (err) {
      throw new Error(`src/app directory not found at ${srcAppPath}`);
    }
    
    // Find all page.tsx files
    const pageFiles = await findPageFiles(srcAppPath, srcAppPath);
    
    if (pageFiles.length === 0) {
      throw new Error('No page.tsx files found in src/app');
    }
    
    // Sort routes for consistent output
    const routes = pageFiles
      .map(file => file.route)
      .sort((a, b) => {
        // Sort by length first, then alphabetically
        if (a.length !== b.length) {
          return a.length - b.length;
        }
        return a.localeCompare(b);
      });
    
    console.log(`\n📋 Found ${routes.length} routes:`);
    routes.forEach(route => {
      console.log(`  ${route}`);
    });
    
    // Generate module.routes.json content
    const routesConfig = {
      routes: routes,
      mountPath: mountPath,
      metadata: {
        description: "Auto-generated module routes",
        version: "1.0.0",
        lastUpdated: new Date().toISOString(),
        generatedBy: "generate-module-routes.mjs"
      }
    };
    
    // Write to file
    const outputPath = path.join(rootDir, 'src', 'platform-integration', 'module.routes.json');
    await fs.writeFile(outputPath, JSON.stringify(routesConfig, null, 2));
    
    console.log(`\n✅ Module routes written to: ${outputPath}`);
    
    // Update module.json if it exists
    const moduleJsonPath = path.join(rootDir, 'module.json');
    try {
      const moduleJson = JSON.parse(await fs.readFile(moduleJsonPath, 'utf-8'));
      moduleJson.mountPath = mountPath;
      moduleJson.routes = routes;
      
      await fs.writeFile(moduleJsonPath, JSON.stringify(moduleJson, null, 2));
      console.log(`✅ Updated module.json with new routes`);
    } catch (err) {
      console.log(`ℹ️  module.json not found or could not be updated: ${err.message}`);
    }
    
    // Update module-descriptor.ts
    const moduleDescriptorPath = path.join(rootDir, 'src', 'platform-integration', 'module-descriptor.ts');
    try {
      let descriptorContent = await fs.readFile(moduleDescriptorPath, 'utf-8');
      
      // Update routeBasePath to match mountPath
      const routeBasePathRegex = /routeBasePath:\s*['"]([^'"]+)['"]/;
      if (routeBasePathRegex.test(descriptorContent)) {
        descriptorContent = descriptorContent.replace(routeBasePathRegex, `routeBasePath: '${mountPath}'`);
        await fs.writeFile(moduleDescriptorPath, descriptorContent);
        console.log(`✅ Updated module-descriptor.ts with new routeBasePath`);
      }
    } catch (err) {
      console.log(`ℹ️  module-descriptor.ts not found or could not be updated: ${err.message}`);
    }
    
    console.log('\n🎉 Module routes generated successfully!');
    
  } catch (error) {
    console.error(`\n❌ Error: ${error.message}`);
    process.exit(1);
  } finally {
    rl.close();
  }
}

// Run the script
generateModuleRoutes();
