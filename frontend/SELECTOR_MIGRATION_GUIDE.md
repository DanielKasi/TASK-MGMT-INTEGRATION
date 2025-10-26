# Selector Migration Guide

## Problem

Your module's selectors don't work when integrated into a host platform because the Redux store structure changes:

**Standalone Mode:**
```typescript
{
  auth: { user: {...}, loading: false },
  miscellaneous: { sideBarOpened: true }
}
```

**Integrated Mode:**
```typescript
{
  auth: { user: {...}, loading: false },           // Host slice
  miscellaneous: { sideBarOpened: true },          // Host slice
  taskManagementAuth: { user: {...}, loading: false },      // Module slice
  taskManagementMisc: { sideBarOpened: true }               // Module slice
}
```

## Solution

Use context-aware selectors that automatically detect the mode and use the correct slice.

## Migration Steps

### Step 1: Update Your Imports

**OLD (won't work in integrated mode):**
```typescript
import {
  selectAccessToken,
  selectSelectedInstitution,
  selectUser,
  selectUserLoading,
} from "@/store/auth/selectors-context-aware";
```

**NEW (works in both modes):**
```typescript
import {
  selectAccessTokenContextAware,
  selectSelectedInstitutionContextAware,
  selectUserContextAware,
  selectUserLoadingContextAware,
} from "@/platform/v1/auth";
```

### Step 2: Update Your Components

**OLD:**
```typescript
function MyComponent() {
  const user = useSelector(selectUser);
  const loading = useSelector(selectUserLoading);
  const token = useSelector(selectAccessToken);
  const institution = useSelector(selectSelectedInstitution);
  
  return (
    <div>
      {loading ? 'Loading...' : `Hello ${user?.fullname}`}
    </div>
  );
}
```

**NEW:**
```typescript
function MyComponent() {
  const user = useSelector(selectUserContextAware);
  const loading = useSelector(selectUserLoadingContextAware);
  const token = useSelector(selectAccessTokenContextAware);
  const institution = useSelector(selectSelectedInstitutionContextAware);
  
  return (
    <div>
      {loading ? 'Loading...' : `Hello ${user?.fullname}`}
    </div>
  );
}
```

### Step 3: Alternative - Use the Hook Directly

You can also use the context-aware selector hook directly:

```typescript
import { useContextAwareSelector } from '@/platform-integration/context-aware-selectors';

function MyComponent() {
  const user = useContextAwareSelector('auth', (authState) => authState?.user?.value);
  const loading = useContextAwareSelector('auth', (authState) => authState?.user?.loading);
  const token = useContextAwareSelector('auth', (authState) => authState?.accessToken);
  const institution = useContextAwareSelector('auth', (authState) => authState?.selectedInstitution?.value);
  
  return (
    <div>
      {loading ? 'Loading...' : `Hello ${user?.fullname}`}
    </div>
  );
}
```

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

## Migration Script

Here's a script to help you migrate your components:

```bash
#!/bin/bash

# Find all files that import from selectors-context-aware
find src -name "*.tsx" -o -name "*.ts" | xargs grep -l "selectors-context-aware" | while read file; do
  echo "Updating $file..."
  
  # Replace imports
  sed -i 's|from "@/store/auth/selectors-context-aware"|from "@/platform/v1/auth"|g' "$file"
  
  # Replace selector names
  sed -i 's/selectUser/selectUserContextAware/g' "$file"
  sed -i 's/selectAccessToken/selectAccessTokenContextAware/g' "$file"
  sed -i 's/selectSelectedInstitution/selectSelectedInstitutionContextAware/g' "$file"
  sed -i 's/selectUserLoading/selectUserLoadingContextAware/g' "$file"
  sed -i 's/selectAttachedInstitutions/selectAttachedInstitutionsContextAware/g' "$file"
  
  echo "✅ Updated $file"
done

echo "🎉 Migration complete!"
```

## Testing

### Test in Standalone Mode
```bash
npm run dev
# Visit your app and verify selectors work
```

### Test in Integrated Mode
1. Sync your module into a host platform
2. Verify selectors work in the integrated environment
3. Check that data is correctly retrieved from the namespaced slices

## Benefits

✅ **Works in both modes** - Standalone and integrated  
✅ **No code duplication** - Single selector definition  
✅ **Type safe** - Full TypeScript support  
✅ **Automatic detection** - No manual configuration needed  
✅ **Backward compatible** - Existing code continues to work  

## Troubleshooting

### Issue: Selectors return undefined
**Solution**: Check that the slice name is correct and the selector is properly defined.

### Issue: Type errors
**Solution**: Make sure you're importing from the correct path and using the correct selector names.

### Issue: Performance issues
**Solution**: The context-aware selectors are optimized, but if you have performance issues, consider using the hook directly for specific cases.

## Example Migration

**Before:**
```typescript
import { useSelector } from 'react-redux';
import {
  selectUser,
  selectUserLoading,
} from "@/store/auth/selectors-context-aware";

function UserProfile() {
  const user = useSelector(selectUser);
  const loading = useSelector(selectUserLoading);
  
  if (loading) return <div>Loading...</div>;
  return <div>Hello {user?.fullname}</div>;
}
```

**After:**
```typescript
import { useSelector } from 'react-redux';
import {
  selectUserContextAware,
  selectUserLoadingContextAware,
} from "@/platform/v1/auth";

function UserProfile() {
  const user = useSelector(selectUserContextAware);
  const loading = useSelector(selectUserLoadingContextAware);
  
  if (loading) return <div>Loading...</div>;
  return <div>Hello {user?.fullname}</div>;
}
```

This ensures your selectors work correctly in both standalone and integrated modes!
