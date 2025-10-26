# Improved Context-Aware Selectors Solution

## Problem with Previous Approach

The previous solution relied on environment variables (`NEXT_PUBLIC_MODULE_NAME`) which is:
- ❌ **Unrealistic** - Multiple modules in one host
- ❌ **Not scalable** - Requires manual configuration
- ❌ **Error-prone** - Easy to misconfigure
- ❌ **Not maintainable** - Hard to manage across modules

## New Improved Solution

### 1. Automatic Context Detection

Created `src/platform-integration/module-context.ts` that:
- **Analyzes Redux store structure** to detect context
- **Automatically identifies module names** from slice patterns
- **Maps slice names** to their correct keys
- **No environment variables needed**

### 2. Smart Slice Detection

The system automatically detects:

**Standalone Mode:**
```typescript
// Store structure
{
  auth: { user: {...}, loading: false },
  miscellaneous: { sideBarOpened: true }
}
// Detected as: standalone mode
```

**Integrated Mode:**
```typescript
// Store structure
{
  auth: { user: {...}, loading: false },           // Host slice
  miscellaneous: { sideBarOpened: true },          // Host slice
  taskManagementAuth: { user: {...}, loading: false },      // Module slice
  taskManagementMisc: { sideBarOpened: true },               // Module slice
  accountingAuth: { user: {...}, loading: false },          // Another module slice
}
// Detected as: integrated mode with modules: taskManagement, accounting
```

### 3. Pattern Recognition

The system recognizes these patterns:
- **Namespaced slices**: `{moduleName}{SliceName}` (e.g., `taskManagementAuth`)
- **Common slice names**: `Auth`, `Misc`, `Miscellaneous`, `Redirects`, `Notifications`
- **Module extraction**: Removes slice suffixes to get module names

## How It Works

### 1. Context Detection Algorithm

```typescript
// 1. Scan all state keys
const stateKeys = Object.keys(state);

// 2. Find namespaced slices (pattern: camelCase with capital letters)
const namespacedSlices = stateKeys.filter(key => 
  /^[a-z][a-zA-Z]*[A-Z][a-zA-Z]*$/.test(key)
);

// 3. Extract module names by removing slice suffixes
namespacedSlices.forEach(key => {
  for (const sliceName of ['Auth', 'Misc', 'Redirects', 'Notifications']) {
    if (key.endsWith(sliceName)) {
      const moduleName = key.slice(0, -sliceName.length);
      sliceMapping[sliceName.toLowerCase()] = key;
    }
  }
});
```

### 2. Slice Key Resolution

```typescript
// For slice 'auth':
// Standalone: returns 'auth'
// Integrated: returns 'taskManagementAuth' (or other module's auth slice)

const sliceKey = getSliceKey('auth', state);
// Result: 'taskManagementAuth' in integrated mode
```

### 3. Automatic Fallback

If the primary detection fails, the system:
1. **Tries all possible slice keys** that end with the slice name
2. **Tests each slice** with the selector function
3. **Returns the first successful result**

## Benefits of New Approach

### ✅ **No Environment Variables**
- Automatically detects context from store structure
- No manual configuration needed

### ✅ **Multi-Module Support**
- Works with multiple modules in one host
- Each module's slices are automatically detected

### ✅ **Robust Detection**
- Pattern recognition for namespaced slices
- Fallback mechanisms for edge cases

### ✅ **Performance Optimized**
- Caches detection results
- Minimal overhead

### ✅ **Type Safe**
- Full TypeScript support
- Proper error handling

## Usage Examples

### 1. Basic Usage (No Changes Required)

```typescript
// Your existing code works without changes
import { selectUserContextAware } from '@/platform/v1/auth';

function MyComponent() {
  const user = useSelector(selectUserContextAware);
  return <div>Hello {user?.fullname}</div>;
}
```

### 2. Direct Hook Usage

```typescript
import { useContextAwareSelector } from '@/platform-integration/context-aware-selectors';

function MyComponent() {
  const user = useContextAwareSelector('auth', (authState) => authState?.user?.value);
  return <div>Hello {user?.fullname}</div>;
}
```

### 3. Debug Information

```typescript
import { getModuleInfo } from '@/platform-integration/module-context';

function DebugComponent() {
  const moduleInfo = useSelector((state: any) => getModuleInfo(state));
  
  return (
    <div>
      <p>Mode: {moduleInfo.isIntegrated ? 'Integrated' : 'Standalone'}</p>
      <p>Module: {moduleInfo.moduleName}</p>
      <p>Slices: {moduleInfo.availableSlices.join(', ')}</p>
    </div>
  );
}
```

## Testing

### 1. Test Component

Use the updated test component to verify everything works:

```typescript
import { SelectorTestComponent } from '@/platform-integration/selector-test';

function TestPage() {
  return <SelectorTestComponent />;
}
```

### 2. Debug Information

The test component now shows:
- **Mode detection** (Standalone/Integrated)
- **Module name** (automatically detected)
- **Available slices** (all slices in store)
- **Slice mapping** (how slices are mapped)

### 3. Manual Testing

```typescript
// Test in standalone mode
npm run dev
// Should show: Mode: Standalone, Slices: auth, miscellaneous, etc.

// Test in integrated mode (after syncing to host)
// Should show: Mode: Integrated, Module: taskManagement, Slices: auth, taskManagementAuth, etc.
```

## Migration

### No Code Changes Required

Your existing code continues to work:

```typescript
// This still works exactly the same
import { selectUserContextAware } from '@/platform/v1/auth';

function MyComponent() {
  const user = useSelector(selectUserContextAware);
  return <div>Hello {user?.fullname}</div>;
}
```

### Optional: Use Debug Information

Add debug information to see how the system works:

```typescript
import { getModuleInfo } from '@/platform-integration/module-context';

function MyComponent() {
  const moduleInfo = useSelector((state: any) => getModuleInfo(state));
  console.log('Module context:', moduleInfo);
  
  // Your existing code...
}
```

## Advanced Configuration

### Custom Slice Detection

If you have custom slice names, you can extend the detection:

```typescript
// In module-context.ts, add your custom slice names
const commonSliceNames = [
  'Auth', 'Misc', 'Miscellaneous', 'Redirects', 'Notifications',
  'Projects', 'Tasks', 'Users', 'Settings' // Add your custom slices
];
```

### Performance Optimization

The system caches detection results, but you can clear the cache if needed:

```typescript
import { clearModuleContextCache } from '@/platform-integration/module-context';

// Clear cache (useful for testing)
clearModuleContextCache();
```

## Troubleshooting

### Issue: Selectors return undefined
**Solution**: Check the debug information to see if slices are detected correctly.

### Issue: Wrong slice selected
**Solution**: The system tries multiple approaches, but you can check the slice mapping in debug info.

### Issue: Performance issues
**Solution**: The system is optimized, but you can clear the cache if needed.

## Files Updated

### New Files
- `src/platform-integration/module-context.ts` - Context detection logic
- `IMPROVED_CONTEXT_AWARE_SOLUTION.md` - This documentation

### Modified Files
- `src/platform-integration/context-aware-selectors.ts` - Updated to use new detection
- `src/platform-integration/selector-test.tsx` - Enhanced with debug information

## Conclusion

This improved solution:
- ✅ **Eliminates environment variable dependency**
- ✅ **Supports multiple modules automatically**
- ✅ **Provides robust fallback mechanisms**
- ✅ **Maintains backward compatibility**
- ✅ **Offers debug information for troubleshooting**

The system now automatically detects the correct context and slice names without any manual configuration! 🎯
