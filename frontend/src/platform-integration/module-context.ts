/**
 * Module Context Detection
 * 
 * This module provides utilities to detect the current module context
 * and determine the correct slice names for context-aware selectors.
 */

// Cache for module context detection
let moduleContextCache: {
  isIntegrated: boolean;
  moduleName: string | null;
  sliceMapping: Record<string, string>;
} | null = null;

/**
 * Detects the current module context by analyzing the Redux store structure
 */
export function detectModuleContext(state: any): {
  isIntegrated: boolean;
  moduleName: string | null;
  sliceMapping: Record<string, string>;
} {
  if (moduleContextCache) {
    return moduleContextCache;
  }

  const sliceMapping: Record<string, string> = {};
  let moduleName: string | null = null;
  let isIntegrated = false;

  // Get all slice keys from the state
  const stateKeys = Object.keys(state || {});
  
  // Look for patterns that indicate integrated mode
  // Pattern: {moduleName}{SliceName} (e.g., taskManagementAuth, accountingAuth)
  const namespacedSlices = stateKeys.filter(key => {
    // Check if this looks like a namespaced slice
    // Should be camelCase with at least one capital letter after the first word
    return /^[a-z][a-zA-Z]*[A-Z][a-zA-Z]*$/.test(key);
  });

  if (namespacedSlices.length > 0) {
    isIntegrated = true;
    
    // Find the most common prefix among namespaced slices
    // This represents the module name
    const commonPrefixes = new Map<string, number>();
    
    namespacedSlices.forEach(key => {
      // Try different prefix lengths to find common patterns
      for (let i = 1; i < key.length; i++) {
        const prefix = key.substring(0, i);
        const remaining = key.substring(i);
        
        // Check if the remaining part looks like a slice name (starts with capital)
        if (/^[A-Z]/.test(remaining)) {
          commonPrefixes.set(prefix, (commonPrefixes.get(prefix) || 0) + 1);
        }
      }
    });

    // Find the prefix with the highest count (most likely module name)
    let maxCount = 0;
    for (const [prefix, count] of commonPrefixes) {
      if (count > maxCount) {
        maxCount = count;
        moduleName = prefix;
      }
    }

    // Build slice mapping for the detected module
    if (moduleName) {
      const moduleSlices = namespacedSlices.filter(key => key.startsWith(moduleName!));
      moduleSlices.forEach(sliceKey => {
        const sliceName = sliceKey.substring(moduleName!.length);
        sliceMapping[sliceName.toLowerCase()] = sliceKey;
      });
    }
  }

  // Cache the result
  moduleContextCache = {
    isIntegrated,
    moduleName,
    sliceMapping,
  };

  return moduleContextCache;
}

/**
 * Gets the correct slice key for a given slice name in the current context
 */
export function getSliceKey(sliceName: string, state: any): string | null {
  const context = detectModuleContext(state);
  
  // If not integrated, use direct slice name
  if (!context.isIntegrated) {
    return sliceName;
  }

  // If integrated, look for namespaced slice
  const namespacedKey = context.sliceMapping[sliceName.toLowerCase()];
  if (namespacedKey) {
    return namespacedKey;
  }

  // Fallback: try to find any slice that ends with the capitalized slice name
  const stateKeys = Object.keys(state || {});
  const possibleKeys = stateKeys.filter(key => 
    key.endsWith(capitalize(sliceName)) && 
    key !== sliceName
  );

  return possibleKeys.length > 0 ? possibleKeys[0] : null;
}

/**
 * Clears the module context cache (useful for testing)
 */
export function clearModuleContextCache(): void {
  moduleContextCache = null;
}

/**
 * Helper to capitalize first letter
 */
function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

/**
 * Gets module information from the current context
 */
export function getModuleInfo(state: any): {
  isIntegrated: boolean;
  moduleName: string | null;
  availableSlices: string[];
  sliceMapping: Record<string, string>;
} {
  const context = detectModuleContext(state);
  const availableSlices = Object.keys(state || {});
  
  return {
    ...context,
    availableSlices,
  };
}
