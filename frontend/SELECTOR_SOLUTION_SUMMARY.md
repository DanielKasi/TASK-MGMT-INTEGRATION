# Context-Aware Selectors Solution Summary

## Problem Solved

Your module's selectors don't work when integrated into a host platform because the Redux store structure changes between standalone and integrated modes.

## Solution Implemented

### 1. Context-Aware Selector Factory
Created `src/platform-integration/context-aware-selectors.ts` that:
- Automatically detects standalone vs integrated mode
- Uses the correct slice based on the context
- Provides fallback mechanisms for robustness

### 2. Updated Context-Aware Selectors
Updated existing selectors to use the new factory:
- `src/store/auth/selectors-context-aware.ts`
- `src/store/miscellaneous/selectors-context-aware.ts`

### 3. Platform API Integration
Updated `src/platform/v1/auth/index.ts` to export context-aware selectors with `ContextAware` suffix.

### 4. Migration Tools
Created tools to help migrate your components:
- `scripts/migrate-selectors.sh` - Automated migration script
- `SELECTOR_MIGRATION_GUIDE.md` - Step-by-step guide
- `src/platform-integration/selector-test.tsx` - Test component

## How It Works

### Standalone Mode
```typescript
// Store structure
{
  auth: { user: {...}, loading: false },
  miscellaneous: { sideBarOpened: true }
}

// Selectors access: state.auth, state.miscellaneous
```

### Integrated Mode
```typescript
// Store structure
{
  auth: { user: {...}, loading: false },           // Host slice
  miscellaneous: { sideBarOpened: true },          // Host slice
  taskManagementAuth: { user: {...}, loading: false },      // Module slice
  taskManagementMisc: { sideBarOpened: true }               // Module slice
}

// Selectors automatically detect and use: state.taskManagementAuth, state.taskManagementMisc
```

## Usage

### Option 1: Platform API Selectors (Recommended)
```typescript
import {
  selectUserContextAware,
  selectUserLoadingContextAware,
  selectAccessTokenContextAware,
} from '@/platform/v1/auth';

function MyComponent() {
  const user = useSelector(selectUserContextAware);
  const loading = useSelector(selectUserLoadingContextAware);
  const token = useSelector(selectAccessTokenContextAware);
  
  return <div>Hello {user?.fullname}</div>;
}
```

### Option 2: Direct Hook Usage
```typescript
import { useContextAwareSelector } from '@/platform-integration/context-aware-selectors';

function MyComponent() {
  const user = useContextAwareSelector('auth', (authState) => authState?.user?.value);
  const loading = useContextAwareSelector('auth', (authState) => authState?.user?.loading);
  
  return <div>Hello {user?.fullname}</div>;
}
```

## Migration Steps

### 1. Run the Migration Script
```bash
./scripts/migrate-selectors.sh
```

### 2. Update Your Components
Replace:
```typescript
// OLD
import { selectUser, selectUserLoading } from "@/store/auth/selectors-context-aware";
```

With:
```typescript
// NEW
import { selectUserContextAware, selectUserLoadingContextAware } from "@/platform/v1/auth";
```

### 3. Test Both Modes
- **Standalone**: `npm run dev` - should work as before
- **Integrated**: Sync into host platform - should work with namespaced slices

## Available Context-Aware Selectors

### Auth Selectors
- `selectUserContextAware`
- `selectAccessTokenContextAware`
- `selectSelectedInstitutionContextAware`
- `selectUserLoadingContextAware`
- `selectAttachedInstitutionsContextAware`
- `selectAuthErrorContextAware`
- `selectRefreshTokenContextAware`
- `selectSelectedBranchContextAware`
- `selectSelectedTillContextAware`
- `selectTemporaryPermissionsContextAware`
- `selectInactivityTimeoutContextAware`
- `selectLogoutWarningVisibleContextAware`
- `selectRefreshInProgressContextAware`

### Miscellaneous Selectors
- `selectSideBarOpenedContextAware`
- `selectSelectedTaskContextAware`

## Testing

### Test Component
Use `src/platform-integration/selector-test.tsx` to verify selectors work:

```typescript
import { SelectorTestComponent } from '@/platform-integration/selector-test';

function TestPage() {
  return (
    <div>
      <h1>Selector Test</h1>
      <SelectorTestComponent />
    </div>
  );
}
```

### Test Hook
```typescript
import { useSelectorTest } from '@/platform-integration/selector-test';

function MyComponent() {
  const { user, loading, isAuthenticated } = useSelectorTest();
  
  return (
    <div>
      {loading ? 'Loading...' : `Hello ${user?.fullname}`}
    </div>
  );
}
```

## Benefits

✅ **Works in both modes** - Standalone and integrated  
✅ **No code duplication** - Single selector definition  
✅ **Type safe** - Full TypeScript support  
✅ **Automatic detection** - No manual configuration needed  
✅ **Backward compatible** - Existing code continues to work  
✅ **Performance optimized** - Efficient selector implementation  
✅ **Fallback mechanisms** - Robust error handling  

## Troubleshooting

### Issue: Selectors return undefined
**Solution**: Check that the slice name is correct and the selector is properly defined.

### Issue: Type errors
**Solution**: Make sure you're importing from the correct path and using the correct selector names.

### Issue: Performance issues
**Solution**: The context-aware selectors are optimized, but if you have performance issues, consider using the hook directly for specific cases.

## Next Steps

1. **Run the migration script** to update your components
2. **Test in standalone mode** to ensure everything works
3. **Test in integrated mode** by syncing into a host platform
4. **Remove old selector imports** once migration is complete
5. **Update documentation** to reflect the new selector usage

## Files Created/Modified

### New Files
- `src/platform-integration/context-aware-selectors.ts` - Core factory
- `scripts/migrate-selectors.sh` - Migration script
- `SELECTOR_MIGRATION_GUIDE.md` - Migration guide
- `src/platform-integration/selector-test.tsx` - Test component
- `SELECTOR_SOLUTION_SUMMARY.md` - This summary

### Modified Files
- `src/store/auth/selectors-context-aware.ts` - Updated import
- `src/store/miscellaneous/selectors-context-aware.ts` - Updated import
- `src/platform/v1/auth/index.ts` - Added context-aware exports

This solution ensures your selectors work correctly in both standalone and integrated modes! 🎯
