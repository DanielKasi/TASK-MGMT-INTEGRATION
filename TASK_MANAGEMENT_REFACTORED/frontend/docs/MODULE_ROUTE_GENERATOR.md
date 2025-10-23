# Module Route Generator

## Overview

The `generate-module-routes.mjs` script automatically scans your `src/app` directory for `page.tsx` files and generates the module routes configuration. This eliminates the need to manually maintain route lists.

## Usage

```bash
node scripts/generate-module-routes.mjs
```

## What It Does

1. **Prompts for Mount Path**: Asks you to enter the mount path for your module
2. **Validates Mount Path**: Ensures the mount path follows naming conventions
3. **Scans for Routes**: Recursively finds all `page.tsx` files in `src/app`
4. **Generates Routes**: Converts file paths to Next.js route patterns
5. **Updates Configuration**: Updates both `module.routes.json` and `module.json`

## Mount Path Validation

The script validates mount paths with these rules:

- ✅ **No spaces allowed**: `task-management` ✅, `task management` ❌
- ✅ **Lowercase only**: `task-management` ✅, `Task-Management` ❌
- ✅ **Letters, numbers, hyphens**: `task-management` ✅, `task_management` ❌
- ✅ **Must start with letter**: `task-management` ✅, `123tasks` ❌
- ✅ **Auto-adds leading slash**: `task-management` → `/task-management`

## Examples

### Valid Mount Paths
```bash
tasks
accounting
user-management
hr-system
project-tracking
```

### Invalid Mount Paths
```bash
task management    # Contains spaces
Task Management    # Contains spaces and uppercase
task_management    # Contains underscore
123tasks          # Starts with number
task.management    # Contains dot
```

## Generated Files

### 1. `src/platform-integration/module.routes.json`
```json
{
  "routes": [
    "/",
    "/(main_app)/(auth)/login",
    "/(main_app)/(dashboard)/dashboard",
    "/projects",
    "/projects/[id]",
    "/task-mgt/task"
  ],
  "mountPath": "/task-management",
  "metadata": {
    "description": "Auto-generated module routes",
    "version": "1.0.0",
    "lastUpdated": "2024-12-19T10:30:00.000Z",
    "generatedBy": "generate-module-routes.mjs"
  }
}
```

### 2. `module.json` (Updated)
```json
{
  "name": "task-management",
  "version": "1.0.0",
  "platformVersion": ">=1.0.0 <2.0.0",
  "mountPath": "/task-management",
  "routes": [
    "/",
    "/(main_app)/(auth)/login",
    "/(main_app)/(dashboard)/dashboard"
  ]
}
```

## Route Generation Logic

The script converts file paths to routes using these rules:

### File Path → Route Mapping
```
src/app/page.tsx                           → /
src/app/(main_app)/(dashboard)/page.tsx    → /(main_app)/(dashboard)
src/app/projects/page.tsx                  → /projects
src/app/projects/[id]/page.tsx             → /projects/[id]
src/app/users/[userId]/page.tsx            → /users/[userId]
```

### Special Cases
- **Root route**: `src/app/page.tsx` → `/`
- **Dynamic routes**: `[id]` segments are preserved
- **Route groups**: `(group)` segments are preserved
- **Nested routes**: Full path structure is maintained

## Integration with Development Workflow

### When to Run
- ✅ **After adding new pages**: When you create new `page.tsx` files
- ✅ **Before syncing to host**: Ensure routes are up-to-date
- ✅ **During module setup**: Initial route configuration
- ✅ **After restructuring**: When moving or renaming pages

### Development Process
```bash
# 1. Create new page
mkdir -p src/app/new-feature
echo "export default function NewFeature() { return <div>New Feature</div>; }" > src/app/new-feature/page.tsx

# 2. Generate updated routes
node scripts/generate-module-routes.mjs

# 3. Commit changes
git add src/platform-integration/module.routes.json module.json
git commit -m "feat: add new-feature route"
```

## Error Handling

The script handles various error conditions:

### Missing src/app Directory
```
❌ Error: src/app directory not found at /path/to/src/app
```

### No page.tsx Files Found
```
❌ Error: No page.tsx files found in src/app
```

### Invalid Mount Path
```
❌ Mount path cannot contain spaces
Please try again.
```

### File System Errors
```
Warning: Could not read directory /path/to/dir: Permission denied
```

## Advanced Usage

### Non-Interactive Mode (for CI/CD)
```bash
echo "my-module" | node scripts/generate-module-routes.mjs
```

### Custom Mount Path Examples
```bash
# Accounting module
echo "accounting" | node scripts/generate-module-routes.mjs

# HR Management module  
echo "hr-management" | node scripts/generate-module-routes.mjs

# Project tracking module
echo "project-tracking" | node scripts/generate-module-routes.mjs
```

## Troubleshooting

### Issue: Script doesn't find expected routes
**Solution**: Check that your `page.tsx` files are in the correct location within `src/app`

### Issue: Mount path validation fails
**Solution**: Ensure mount path follows the naming rules (lowercase, no spaces, starts with letter)

### Issue: Generated routes look wrong
**Solution**: Verify your Next.js app router structure follows conventions

### Issue: Script hangs on input
**Solution**: Use non-interactive mode with echo: `echo "mount-path" | node scripts/generate-module-routes.mjs`

## Best Practices

1. **Run regularly**: Update routes when adding new pages
2. **Review generated routes**: Check that all routes are correct
3. **Use descriptive mount paths**: Choose clear, meaningful names
4. **Follow naming conventions**: Use kebab-case for mount paths
5. **Commit route changes**: Include route updates in your commits

## Integration with Other Scripts

This script works seamlessly with:

- **`sync-module.mjs`**: Uses generated routes for host integration
- **`validate-routes.mjs`**: Validates generated routes for conflicts
- **Module descriptor**: Routes are used in module integration

## Future Enhancements

Potential improvements for future versions:

- **Route filtering**: Exclude certain routes (e.g., admin-only routes)
- **Route categorization**: Group routes by feature area
- **Custom route patterns**: Support for custom route transformations
- **Route validation**: Check for Next.js route conventions
- **Interactive route selection**: Choose which routes to include
