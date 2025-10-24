#!/bin/bash

# Module Repository Preparation Script
# This script prepares the current module for repository creation and sync testing

set -e

echo "🚀 Preparing Task Management Module for Repository Creation"
echo "=========================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "module.json" ]; then
    print_error "module.json not found. Please run this script from the module root directory."
    exit 1
fi

print_info "Current directory: $(pwd)"

# Create temporary directory for module preparation
TEMP_DIR="/tmp/task-management-module-$(date +%s)"
MODULE_NAME="task-management"
MODULE_VERSION="1.0.0"

print_info "Creating temporary directory: $TEMP_DIR"
mkdir -p "$TEMP_DIR"

# Copy essential module files
print_info "Copying module files..."

# Core module files
cp module.json "$TEMP_DIR/"
cp package.json "$TEMP_DIR/"
cp tsconfig.json "$TEMP_DIR/"
cp tailwind.config.ts "$TEMP_DIR/"
cp next.config.mjs "$TEMP_DIR/"
cp postcss.config.mjs "$TEMP_DIR/"
cp components.json "$TEMP_DIR/"

# Copy src directory (module core)
print_info "Copying src directory..."
cp -r src "$TEMP_DIR/"

# Copy public directory
if [ -d "public" ]; then
    print_info "Copying public directory..."
    cp -r public "$TEMP_DIR/"
fi

# Copy standalone app directory (if exists)
if [ -d "app" ]; then
    print_info "Copying standalone app directory..."
    cp -r app "$TEMP_DIR/"
fi

# Copy documentation files
print_info "Copying documentation..."
cp README.md "$TEMP_DIR/" 2>/dev/null || print_warning "README.md not found, will create one"
cp MODULE_README.md "$TEMP_DIR/" 2>/dev/null || print_warning "MODULE_README.md not found"
cp MIGRATION_GUIDE.md "$TEMP_DIR/" 2>/dev/null || print_warning "MIGRATION_GUIDE.md not found"

# Create module-specific files
print_info "Creating module-specific files..."

# Create .gitignore for module
cat > "$TEMP_DIR/.gitignore" << 'EOF'
# Dependencies
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Next.js
.next/
out/
build/

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Runtime data
pids
*.pid
*.seed
*.pid.lock

# Coverage directory used by tools like istanbul
coverage/

# Temporary folders
tmp/
temp/

# Module-specific
modules.lock.json
EOF

# Create module README
cat > "$TEMP_DIR/README.md" << EOF
# Task Management Module

A comprehensive task management module for the modular platform architecture.

## Overview

This module provides:
- Task creation and management
- Project tracking and collaboration
- User management and roles
- Administrative features
- Analytics and reporting

## Module Information

- **Name**: task-management
- **Version**: $MODULE_VERSION
- **Platform Version**: >=1.0.0 <2.0.0
- **Mount Path**: /task-management

## Routes

The module provides the following routes:
- \`/\` - Landing page
- \`/dashboard\` - Main dashboard
- \`/projects\` - Project management
- \`/task-mgt/task\` - Task management
- \`/admin\` - Administrative features
- And many more...

## Development

### Prerequisites
- Node.js 18+
- npm or yarn
- Access to platform API

### Installation
\`\`\`bash
npm install
\`\`\`

### Development Mode
\`\`\`bash
npm run dev
\`\`\`

### Build
\`\`\`bash
npm run build
\`\`\`

## Integration

This module is designed to be integrated into a host platform using the sync script:

\`\`\`bash
node scripts/sync-module.mjs \\
  --repo "https://github.com/yourorg/task-management-module" \\
  --tag "v$MODULE_VERSION" \\
  --name "task-management"
\`\`\`

## Architecture

This module follows the modular platform architecture:
- Uses platform API (\`@/platform/v1\`)
- Provides Redux slices and sagas
- Implements context-aware state management
- Supports both standalone and integrated modes

## License

[Add your license here]
EOF

# Create module package.json (simplified for module)
print_info "Creating module package.json..."
cat > "$TEMP_DIR/package.json" << EOF
{
  "name": "task-management-module",
  "version": "$MODULE_VERSION",
  "description": "Comprehensive task management module for the modular platform architecture",
  "main": "src/platform-integration/module-descriptor.ts",
  "scripts": {
    "dev": "next dev --turbopack",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "type-check": "tsc --noEmit"
  },
  "keywords": [
    "task-management",
    "project-management",
    "modular-platform",
    "nextjs",
    "redux"
  ],
  "author": "Task Management Team",
  "license": "MIT",
  "peerDependencies": {
    "react": "^19.1.0",
    "react-dom": "^19.1.0",
    "next": "^15.2.4",
    "@reduxjs/toolkit": "^2.7.0",
    "redux-saga": "^1.3.0",
    "redux-persist": "^6.0.0",
    "@tanstack/react-query": "^5.86.0",
    "tailwindcss": "^3.4.17",
    "lucide-react": "^0.454.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "@types/react": "^18.0.0",
    "@types/react-dom": "^18.0.0",
    "typescript": "^5.0.0",
    "eslint": "^8.0.0",
    "eslint-config-next": "^15.2.4"
  }
}
EOF

# Create GitHub Actions workflow for module releases
print_info "Creating GitHub Actions workflow..."
mkdir -p "$TEMP_DIR/.github/workflows"
cat > "$TEMP_DIR/.github/workflows/release.yml" << 'EOF'
name: Release Module

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Type check
        run: npm run type-check
      
      - name: Build
        run: npm run build
      
      - name: Create Release
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag_name: ${{ github.ref }}
          release_name: Release ${{ github.ref }}
          draft: false
          prerelease: false
      
      - name: Notify Host Platform
        run: |
          curl -X POST \
            -H "Authorization: token ${{ secrets.HOST_PLATFORM_TOKEN }}" \
            -H "Accept: application/vnd.github.v3+json" \
            https://api.github.com/repos/${{ secrets.HOST_PLATFORM_REPO }}/dispatches \
            -d '{"event_type":"module-release","client_payload":{"module_name":"task-management","module_tag":"${{ github.ref_name }}","module_repo":"${{ github.repository }}"}}'
EOF

# Create module validation script
print_info "Creating module validation script..."
mkdir -p "$TEMP_DIR/scripts"
cat > "$TEMP_DIR/scripts/validate-module.mjs" << 'EOF'
#!/usr/bin/env node

import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.join(__dirname, '..');

async function validateModule() {
  console.log('\n🔍 Validating Task Management Module\n');

  const errors = [];
  const warnings = [];

  // Check required files
  const requiredFiles = [
    'module.json',
    'src/platform-integration/module-descriptor.ts',
    'src/app',
    'package.json'
  ];

  for (const file of requiredFiles) {
    try {
      await fs.access(path.join(rootDir, file));
      console.log(`✅ ${file} exists`);
    } catch (err) {
      errors.push(`Missing required file: ${file}`);
    }
  }

  // Validate module.json
  try {
    const manifest = JSON.parse(await fs.readFile(path.join(rootDir, 'module.json'), 'utf-8'));
    
    if (!manifest.name) errors.push('module.json missing name');
    if (!manifest.version) errors.push('module.json missing version');
    if (!manifest.platformVersion) errors.push('module.json missing platformVersion');
    if (!manifest.mountPath) errors.push('module.json missing mountPath');
    if (!manifest.routes || !Array.isArray(manifest.routes)) errors.push('module.json missing routes array');
    
    console.log(`✅ module.json is valid`);
  } catch (err) {
    errors.push(`Invalid module.json: ${err.message}`);
  }

  // Validate module descriptor
  try {
    const descriptorPath = path.join(rootDir, 'src/platform-integration/module-descriptor.ts');
    await fs.access(descriptorPath);
    console.log(`✅ module-descriptor.ts exists`);
  } catch (err) {
    errors.push('Missing module-descriptor.ts');
  }

  // Check for platform API usage
  try {
    const srcDir = path.join(rootDir, 'src');
    const files = await fs.readdir(srcDir, { recursive: true });
    
    let platformApiUsage = false;
    for (const file of files) {
      if (file.endsWith('.tsx') || file.endsWith('.ts')) {
        const content = await fs.readFile(path.join(srcDir, file), 'utf-8');
        if (content.includes('@/platform/v1')) {
          platformApiUsage = true;
          break;
        }
      }
    }
    
    if (platformApiUsage) {
      console.log(`✅ Platform API usage detected`);
    } else {
      warnings.push('No platform API usage detected - module may not be properly integrated');
    }
  } catch (err) {
    warnings.push(`Could not check platform API usage: ${err.message}`);
  }

  // Report results
  if (errors.length > 0) {
    console.log('\n❌ Validation Errors:');
    errors.forEach(error => console.log(`  - ${error}`));
  }

  if (warnings.length > 0) {
    console.log('\n⚠️  Warnings:');
    warnings.forEach(warning => console.log(`  - ${warning}`));
  }

  if (errors.length === 0) {
    console.log('\n✅ Module validation passed!');
    console.log('\n📋 Next steps:');
    console.log('1. Initialize git repository: git init');
    console.log('2. Add files: git add .');
    console.log('3. Commit: git commit -m "Initial commit"');
    console.log('4. Create GitHub repository');
    console.log('5. Push: git push origin main');
    console.log('6. Create release tag: git tag v1.0.0 && git push origin v1.0.0');
    console.log('7. Test sync with host platform');
  } else {
    console.log('\n❌ Module validation failed!');
    process.exit(1);
  }
}

validateModule().catch(error => {
  console.error('Validation failed:', error);
  process.exit(1);
});
EOF

# Make validation script executable
chmod +x "$TEMP_DIR/scripts/validate-module.mjs"

# Create sync test script for host platform
print_info "Creating sync test script..."
cat > "$TEMP_DIR/scripts/test-sync.mjs" << 'EOF'
#!/usr/bin/env node

import { execSync } from 'child_process';
import fs from 'fs/promises';
import path from 'path';

async function testSync() {
  console.log('\n🧪 Testing Module Sync Process\n');

  const moduleRepo = process.argv[2] || 'https://github.com/yourorg/task-management-module';
  const moduleTag = process.argv[3] || 'v1.0.0';
  const moduleName = process.argv[4] || 'task-management';

  console.log(`Repository: ${moduleRepo}`);
  console.log(`Tag: ${moduleTag}`);
  console.log(`Name: ${moduleName}`);

  // Test sync command
  const syncCommand = `node scripts/sync-module.mjs --repo "${moduleRepo}" --tag "${moduleTag}" --name "${moduleName}"`;
  
  console.log(`\n📋 Sync Command:`);
  console.log(syncCommand);
  
  console.log(`\n📋 To test sync on host platform:`);
  console.log(`1. Navigate to host platform directory`);
  console.log(`2. Run: ${syncCommand}`);
  console.log(`3. Verify module integration`);
  console.log(`4. Test routes and functionality`);
}

testSync().catch(error => {
  console.error('Test setup failed:', error);
  process.exit(1);
});
EOF

chmod +x "$TEMP_DIR/scripts/test-sync.mjs"

# Create module documentation
print_info "Creating module documentation..."
cat > "$TEMP_DIR/MODULE_INTEGRATION_GUIDE.md" << 'EOF'
# Task Management Module Integration Guide

## Overview

This guide explains how to integrate the Task Management Module into a host platform.

## Module Structure

```
task-management-module/
├── src/
│   ├── app/                          # Next.js app routes
│   ├── components/                   # Module components
│   ├── platform-integration/         # Platform integration files
│   │   ├── module-descriptor.ts      # Module descriptor
│   │   └── module.routes.json        # Route definitions
│   ├── platform/v1/                  # Platform API (re-exports)
│   ├── store/                        # Redux store
│   └── types/                        # TypeScript types
├── app/                              # Standalone app (for development)
├── module.json                       # Module manifest
├── package.json                      # Dependencies
└── README.md                         # Module documentation
```

## Integration Process

### 1. Host Platform Setup

Ensure the host platform has:
- Platform API (`src/platform/v1/`)
- Sync script (`scripts/sync-module.mjs`)
- Store registry (`src/lib/redux/registry.ts`)

### 2. Module Sync

```bash
# From host platform directory
node scripts/sync-module.mjs \
  --repo "https://github.com/yourorg/task-management-module" \
  --tag "v1.0.0" \
  --name "task-management"
```

### 3. Verification

After sync, verify:
- Module routes are accessible
- Redux store includes module slices
- Platform API works correctly
- No route conflicts

## Module Features

- **Task Management**: Create, assign, and track tasks
- **Project Tracking**: Manage projects and milestones
- **User Management**: Handle users and roles
- **Analytics**: Project and task analytics
- **Administration**: System administration features

## Routes

The module provides routes under `/task-management`:
- `/task-management/dashboard` - Main dashboard
- `/task-management/projects` - Project management
- `/task-management/task-mgt/task` - Task management
- `/task-management/admin` - Administrative features

## State Management

Module provides Redux slices:
- `taskManagementAuth` - Authentication state
- `taskManagementMisc` - Miscellaneous state
- `taskManagementRedirects` - Redirect state
- `taskManagementNotifications` - Notification state

## Development

### Standalone Mode

```bash
npm run dev
```

### Integrated Mode

Module automatically detects integration and adjusts behavior.

## Testing

```bash
# Validate module
npm run validate-module

# Test sync process
npm run test-sync
```

## Support

For issues or questions:
1. Check module documentation
2. Review platform API usage
3. Validate module structure
4. Contact module maintainers
EOF

# Create final summary
print_info "Module preparation complete!"
print_status "Module files prepared in: $TEMP_DIR"
print_status "Module name: $MODULE_NAME"
print_status "Module version: $MODULE_VERSION"

echo ""
echo "📋 Next Steps:"
echo "1. Review prepared files in: $TEMP_DIR"
echo "2. Initialize git repository:"
echo "   cd $TEMP_DIR"
echo "   git init"
echo "   git add ."
echo "   git commit -m 'Initial commit'"
echo ""
echo "3. Create GitHub repository and push:"
echo "   git remote add origin <your-repo-url>"
echo "   git push -u origin main"
echo ""
echo "4. Create release tag:"
echo "   git tag v$MODULE_VERSION"
echo "   git push origin v$MODULE_VERSION"
echo ""
echo "5. Test sync on host platform:"
echo "   node scripts/sync-module.mjs \\"
echo "     --repo '<your-repo-url>' \\"
echo "     --tag 'v$MODULE_VERSION' \\"
echo "     --name '$MODULE_NAME'"
echo ""
echo "6. Validate integration:"
echo "   npm run validate-routes"
echo "   npm run build"
echo "   npm run dev"

echo ""
print_info "Module preparation script completed successfully!"
echo "Temporary directory: $TEMP_DIR"
echo "You can now proceed with repository creation and testing."
