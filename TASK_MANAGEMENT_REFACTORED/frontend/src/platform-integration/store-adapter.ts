import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '@/store/rootReducer';

/**
 * Store adapter that provides dual-context compatibility
 * Works in both standalone and integrated modes without code changes
 */

// Detect if we're running in integrated mode
const isIntegratedMode = () => {
  // Check if we're in a host environment by looking for host-specific globals
  return typeof window !== 'undefined' && 
         (window as any).__HOST_PLATFORM__ === true;
};

// Get the module name from environment or default
const getModuleName = () => {
  if (typeof window !== 'undefined' && (window as any).__MODULE_NAME__) {
    return (window as any).__MODULE_NAME__;
  }
  return 'task-management'; // Default module name
};

/**
 * Creates a context-aware selector that works in both standalone and integrated modes
 */
export function createContextAwareSelector<T>(
  sliceName: string,
  selector: (sliceState: any) => T
) {
  return (state: RootState) => {
    if (isIntegratedMode()) {
      // In integrated mode, access the namespaced slice
      const moduleName = getModuleName();
      const namespacedKey = `${moduleName}${sliceName.charAt(0).toUpperCase() + sliceName.slice(1)}`;
      const sliceState = (state as any)[namespacedKey];
      
      if (!sliceState) {
        console.warn(`Slice ${namespacedKey} not found in integrated mode`);
        return undefined;
      }
      
      return selector(sliceState);
    } else {
      // In standalone mode, access the slice directly
      const sliceState = (state as any)[sliceName];
      return selector(sliceState);
    }
  };
}

/**
 * Hook that provides context-aware state access
 * Components can use this instead of useSelector for guaranteed compatibility
 */
export function useModuleSelector<T>(
  sliceName: string,
  selector: (sliceState: any) => T
): T | undefined {
  const contextAwareSelector = createContextAwareSelector(sliceName, selector);
  return useSelector(contextAwareSelector);
}

/**
 * Hook that provides context-aware dispatch
 * Ensures actions are dispatched to the correct slice
 */
export function useModuleDispatch() {
  const dispatch = useDispatch();
  
  return (action: any) => {
    // Actions don't need modification - Redux handles routing to correct slice
    return dispatch(action);
  };
}

/**
 * Store shape validator
 * Ensures the store has the expected structure for the current mode
 */
export function validateStoreShape(state: RootState): boolean {
  if (isIntegratedMode()) {
    const moduleName = getModuleName();
    const expectedSlices = ['auth', 'miscellaneous', 'redirects', 'notifications'];
    
    for (const sliceName of expectedSlices) {
      const namespacedKey = `${moduleName}${sliceName.charAt(0).toUpperCase() + sliceName.slice(1)}`;
      if (!(state as any)[namespacedKey]) {
        console.error(`Expected slice ${namespacedKey} not found in integrated mode`);
        return false;
      }
    }
  } else {
    // In standalone mode, check for direct slice access
    const expectedSlices = ['auth', 'miscellaneous', 'redirects', 'notifications'];
    
    for (const sliceName of expectedSlices) {
      if (!(state as any)[sliceName]) {
        console.error(`Expected slice ${sliceName} not found in standalone mode`);
        return false;
      }
    }
  }
  
  return true;
}

/**
 * Debug utility to inspect store structure
 */
export function inspectStoreStructure(state: RootState): void {
  console.group('🔍 Store Structure Inspection');
  console.log('Mode:', isIntegratedMode() ? 'Integrated' : 'Standalone');
  console.log('Module Name:', getModuleName());
  console.log('Store Keys:', Object.keys(state));
  
  if (isIntegratedMode()) {
    const moduleName = getModuleName();
    const expectedSlices = ['auth', 'miscellaneous', 'redirects', 'notifications'];
    
    expectedSlices.forEach(sliceName => {
      const namespacedKey = `${moduleName}${sliceName.charAt(0).toUpperCase() + sliceName.slice(1)}`;
      const exists = !!(state as any)[namespacedKey];
      console.log(`${namespacedKey}:`, exists ? '✅' : '❌');
    });
  }
  
  console.groupEnd();
}
