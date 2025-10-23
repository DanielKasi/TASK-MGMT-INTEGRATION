# Dual-Context State Management Guide

This document explains how our Redux state management works seamlessly in both standalone and integrated modes.

## Overview

Our modular architecture requires state management that works in two contexts:
- **Standalone Mode**: Module runs independently with its own Redux store
- **Integrated Mode**: Module is embedded in a host platform with a combined store

## The Challenge

The core challenge is that store structure differs between modes:

### Standalone Mode Store Structure
```typescript
{
  auth: AuthState,           // Direct access
  miscellaneous: MiscState,  // Direct access
  redirects: RedirectsState, // Direct access
  notifications: NotificationsState // Direct access
}
```

### Integrated Mode Store Structure
```typescript
{
  // Host slices
  hostAuth: HostAuthState,
  hostSettings: HostSettingsState,
  
  // Module slices (namespaced)
  taskManagementAuth: AuthState,           // Namespaced access
  taskManagementMisc: MiscState,          // Namespaced access
  taskManagementRedirects: RedirectsState, // Namespaced access
  taskManagementNotifications: NotificationsState // Namespaced access
}
```

## Solution: Context-Aware Store Adapter

We've created a store adapter that automatically handles the differences between modes.

### 1. Store Adapter (`src/platform-integration/store-adapter.ts`)

The adapter provides:
- **Mode Detection**: Automatically detects standalone vs integrated mode
- **Context-Aware Selectors**: Work in both modes without code changes
- **Store Validation**: Ensures correct store structure
- **Debug Utilities**: Help inspect store structure

### 2. Context-Aware Selectors

Instead of direct slice access:
```typescript
// ❌ Breaks in integrated mode
const authSlice = (state: RootState) => state.auth;
```

We use context-aware selectors:
```typescript
// ✅ Works in both modes
const authSlice = createContextAwareSelector('auth', (slice) => slice);
```

### 3. Module Descriptor Namespacing

The module descriptor now uses namespaced slice keys:

```typescript
// src/platform-integration/module-descriptor.ts
export const moduleDescriptor: ModuleDescriptor = {
  name: 'task-management',
  slices: {
    // Namespaced for host integration
    'taskManagementAuth': authReducer,
    'taskManagementMisc': miscReducer,
    'taskManagementRedirects': redirectsReducer,
    'taskManagementNotifications': notificationsReducer,
  },
  // ... rest of config
};
```

## Usage Patterns

### Pattern 1: Using Context-Aware Selectors (Recommended)

```typescript
import { 
  selectUserContextAware,
  selectSelectedInstitutionContextAware 
} from '@/platform/v1/auth';

function MyComponent() {
  const user = useSelector(selectUserContextAware);
  const institution = useSelector(selectSelectedInstitutionContextAware);
  
  return (
    <div>
      <h1>{user?.fullname}</h1>
      <p>{institution?.institution_name}</p>
    </div>
  );
}
```

### Pattern 2: Using Store Adapter Directly

```typescript
import { useModuleSelector } from '@/platform-integration/store-adapter';

function MyComponent() {
  const user = useModuleSelector('auth', (authState) => authState?.user?.value);
  const institution = useModuleSelector('auth', (authState) => authState?.selectedInstitution?.value);
  
  return (
    <div>
      <h1>{user?.fullname}</h1>
      <p>{institution?.institution_name}</p>
    </div>
  );
}
```

### Pattern 3: Legacy Selectors (Standalone Only)

```typescript
import { selectUser, selectSelectedInstitution } from '@/platform/v1/auth';

function MyComponent() {
  const user = useSelector(selectUser);           // ❌ Breaks in integrated mode
  const institution = useSelector(selectSelectedInstitution); // ❌ Breaks in integrated mode
  
  return (
    <div>
      <h1>{user?.fullname}</h1>
      <p>{institution?.institution_name}</p>
    </div>
  );
}
```

## Host Integration

### Host Store Configuration

The host platform uses the generated store registry:

```typescript
// Generated: src/lib/redux/store-registry.ts
import { combineReducers } from '@reduxjs/toolkit';
import { all, fork } from 'redux-saga/effects';

import { moduleDescriptor as taskManagement } from './task-management';

// Combine all module slices with namespacing
export const moduleSlices = combineReducers({
  ...taskManagement.slices, // taskManagementAuth, taskManagementMisc, etc.
});

// Combine all module sagas
export function* moduleSagas() {
  yield all([
    ...taskManagement.sagas.map(saga => fork(saga)),
  ]);
}
```

### Host Root Store

```typescript
// Host's rootReducer.ts
import { combineReducers } from '@reduxjs/toolkit';
import { moduleSlices } from '@/lib/redux/store-registry';

const rootReducer = combineReducers({
  // Host slices
  hostAuth: hostAuthReducer,
  hostSettings: hostSettingsReducer,
  
  // Module slices (automatically namespaced)
  ...moduleSlices,
});

export type RootState = ReturnType<typeof rootReducer>;
```

## Migration Strategy

### Phase 1: Update Existing Components (Optional)

For components that need to work in both modes, update selectors:

```typescript
// Before
import { selectUser } from '@/platform/v1/auth';

// After
import { selectUserContextAware } from '@/platform/v1/auth';
```

### Phase 2: New Components

Always use context-aware selectors for new components:

```typescript
import { selectUserContextAware } from '@/platform/v1/auth';
```

### Phase 3: Testing

Test components in both modes:
- **Standalone**: Run module independently
- **Integrated**: Run module within host platform

## Benefits

✅ **Zero Code Changes**: Existing components work without modification in standalone mode
✅ **Seamless Integration**: Components work automatically in integrated mode
✅ **Type Safety**: Full TypeScript support in both contexts
✅ **Performance**: No runtime overhead - all logic is build-time
✅ **Debugging**: Built-in store inspection utilities
✅ **Future-Proof**: Easy to add new modules without conflicts

## Debugging

Use the built-in debugging utilities:

```typescript
import { inspectStoreStructure, validateStoreShape } from '@/platform-integration/store-adapter';

// In a component
useEffect(() => {
  const state = useSelector(state => state);
  inspectStoreStructure(state);
  console.log('Store valid:', validateStoreShape(state));
}, []);
```

## Best Practices

1. **Use Context-Aware Selectors**: Always prefer `selectUserContextAware` over `selectUser`
2. **Test Both Modes**: Ensure components work in standalone and integrated modes
3. **Use Store Adapter**: For complex state access, use `useModuleSelector`
4. **Validate Store**: Use validation utilities in development
5. **Namespace Slices**: Always use namespaced slice keys in module descriptors

## Troubleshooting

### Issue: Selector returns undefined in integrated mode
**Solution**: Use context-aware selectors or check store structure with `inspectStoreStructure`

### Issue: Store validation fails
**Solution**: Ensure module descriptor uses correct namespaced slice keys

### Issue: Actions not dispatching
**Solution**: Actions don't need modification - Redux handles routing to correct slice automatically

### Issue: Saga not running
**Solution**: Ensure sagas are properly exported in module descriptor and forked in host store
