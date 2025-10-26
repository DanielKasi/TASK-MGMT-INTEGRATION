# Context-Aware Selectors Solution

## The Problem

When a module is integrated into a host platform, the Redux store structure changes:

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

## The Solution: Context-Aware Selectors

Create selectors that automatically detect the context and use the appropriate slice.

### 1. Create Context-Aware Selector Factory

Create `src/platform-integration/context-aware-selectors.ts`:

```typescript
import { createSelector } from '@reduxjs/toolkit';
import { useSelector } from 'react-redux';

// This function creates a selector that works in both standalone and integrated modes
export function createContextAwareSelector<T>(
  sliceName: string,
  selector: (sliceState: any) => T
) {
  return (state: any): T | undefined => {
    // Try standalone mode first (direct slice access)
    if (state && state[sliceName]) {
      return selector(state[sliceName]);
    }

    // Try integrated mode (namespaced slice access)
    const moduleName = process.env.NEXT_PUBLIC_MODULE_NAME || 'taskManagement';
    const namespacedKey = `${moduleName}${capitalize(sliceName)}`;
    
    if (state && state[namespacedKey]) {
      return selector(state[namespacedKey]);
    }

    // Fallback: try to find any slice with the selector
    for (const key in state) {
      if (typeof state[key] === 'object' && state[key] !== null) {
        try {
          const result = selector(state[key]);
          if (result !== undefined) {
            return result;
          }
        } catch (err) {
          // Continue searching
        }
      }
    }

    return undefined;
  };
}

// Helper to capitalize first letter
function capitalize(s: string) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

// Hook that provides context-aware state access
export function useContextAwareSelector<T>(
  sliceName: string,
  selector: (sliceState: any) => T
): T | undefined {
  const contextAwareSelector = createContextAwareSelector(sliceName, selector);
  return useSelector(contextAwareSelector);
}
```

### 2. Create Context-Aware Auth Selectors

Create `src/store/auth/selectors-context-aware.ts`:

```typescript
import { createSelector } from '@reduxjs/toolkit';
import { createContextAwareSelector } from '@/platform-integration/context-aware-selectors';
import { AuthState } from './reducer';

// Create context-aware slice selector
const authSlice = createContextAwareSelector<AuthState>('auth', (slice) => slice);

// Context-aware selectors
export const selectUser = createSelector([authSlice], (slice) => slice?.user?.value);
export const selectAuthError = createSelector([authSlice], (slice) => slice?.user?.error);
export const selectUserLoading = createSelector([authSlice], (slice) => slice?.user?.loading);
export const selectAccessToken = createSelector([authSlice], (slice) => slice?.accessToken);
export const selectRefreshToken = createSelector([authSlice], (slice) => slice?.refreshToken);
export const selectSelectedInstitution = createSelector([authSlice], (slice) => slice?.selectedInstitution?.value);
export const selectSelectedInstitutionLoading = createSelector([authSlice], (slice) => slice?.selectedInstitution?.loading);
export const selectSelectedBranch = createSelector([authSlice], (slice) => slice?.selectedBranch?.value);
export const selectSelectedBranchLoading = createSelector([authSlice], (slice) => slice?.selectedBranch?.loading);
export const selectSelectedTill = createSelector([authSlice], (slice) => slice?.selectedTill?.value);
export const selectSelectedTillLoading = createSelector([authSlice], (slice) => slice?.selectedTill?.loading);
export const selectAttachedInstitutions = createSelector([authSlice], (slice) => slice?.InstitutionsAttached?.value || []);
export const selectAttachedInstitutionsLoading = createSelector([authSlice], (slice) => slice?.InstitutionsAttached?.loading);
export const selectTemporaryPermissions = createSelector([authSlice], (slice) => slice?.temporaryPermissions);
export const selectInactivityTimeout = createSelector([authSlice], (slice) => slice?.inactivityTimeout);
export const selectLogoutWarningVisible = createSelector([authSlice], (slice) => slice?.logoutWarningVisible);
export const selectRefreshInProgress = createSelector([authSlice], (slice) => slice?.refreshInProgress);
```

### 3. Create Context-Aware Misc Selectors

Create `src/store/miscellaneous/selectors-context-aware.ts`:

```typescript
import { createSelector } from '@reduxjs/toolkit';
import { createContextAwareSelector } from '@/platform-integration/context-aware-selectors';
import { MiscState } from './reducer';

// Create context-aware slice selector
const miscSlice = createContextAwareSelector<MiscState>('miscellaneous', (slice) => slice);

// Context-aware selectors
export const selectSideBarOpened = createSelector([miscSlice], (misc) => misc?.sideBarOpened);
export const selectSelectedTask = createSelector([miscSlice], (misc) => misc?.selectedTask);
```

### 4. Update Platform API to Export Context-Aware Selectors

Update `src/platform/v1/auth/index.ts`:

```typescript
// Re-export context-aware selectors
export {
  selectUser as selectUserContextAware,
  selectAccessToken as selectAccessTokenContextAware,
  selectSelectedInstitution as selectSelectedInstitutionContextAware,
  selectUserLoading as selectUserLoadingContextAware,
  selectAttachedInstitutions as selectAttachedInstitutionsContextAware,
} from '@/store/auth/selectors-context-aware';

// Re-export regular selectors for backward compatibility
export {
  selectAccessToken,
  selectSelectedInstitution,
  selectUser,
  selectUserLoading,
  selectAttachedInstitutions,
} from '@/store/auth/selectors';
```

### 5. Update Your Components

Instead of importing from `selectors-context-aware`, import from the platform API:

```typescript
// OLD (won't work in integrated mode)
import {
  selectAccessToken,
  selectSelectedInstitution,
  selectUser,
  selectUserLoading,
} from "@/store/auth/selectors-context-aware";

// NEW (works in both modes)
import {
  selectAccessTokenContextAware,
  selectSelectedInstitutionContextAware,
  selectUserContextAware,
  selectUserLoadingContextAware,
} from "@/platform/v1/auth";
```

### 6. Alternative: Use the Hook Directly

You can also use the hook directly in components:

```typescript
import { useContextAwareSelector } from '@/platform-integration/context-aware-selectors';

function MyComponent() {
  const user = useContextAwareSelector('auth', (authState) => authState?.user?.value);
  const loading = useContextAwareSelector('auth', (authState) => authState?.user?.loading);
  
  return (
    <div>
      {loading ? 'Loading...' : `Hello ${user?.fullname}`}
    </div>
  );
}
```

## Implementation Steps

### Step 1: Create Context-Aware Selector Factory
Create the `context-aware-selectors.ts` file with the factory function.

### Step 2: Create Context-Aware Selectors for Each Slice
Create `selectors-context-aware.ts` for each slice (auth, miscellaneous, etc.).

### Step 3: Update Platform API
Export context-aware selectors from the platform API.

### Step 4: Update Components
Replace direct selector imports with platform API imports.

### Step 5: Test Both Modes
- Test in standalone mode (current project)
- Test in integrated mode (host platform)

## Benefits

✅ **Works in both modes** - Standalone and integrated  
✅ **No code duplication** - Single selector definition  
✅ **Type safe** - Full TypeScript support  
✅ **Automatic detection** - No manual configuration needed  
✅ **Backward compatible** - Existing code continues to work  

## Example Usage

```typescript
// This works in both standalone and integrated modes
import { 
  selectUserContextAware,
  selectAccessTokenContextAware 
} from '@/platform/v1/auth';

function MyComponent() {
  const user = useSelector(selectUserContextAware);
  const token = useSelector(selectAccessTokenContextAware);
  
  return <div>Hello {user?.fullname}</div>;
}
```

This solution ensures your selectors work correctly regardless of whether the module is running standalone or integrated into a host platform.
