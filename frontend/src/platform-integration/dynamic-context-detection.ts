/**
 * Dynamic Context Detection
 * 
 * This module provides a more robust approach to detecting module context
 * by analyzing the actual structure and content of Redux slices rather than
 * relying on naming patterns or hardcoded assumptions.
 */

import { getModuleInfo } from "./module-context";


/**
 * Gets the correct slice key for a given slice name using dynamic detection
 */
export function getDynamicSliceKey(sliceName: string, state: any): string | null {
  const context = getModuleInfo(state);
  console.log("\n\n context", context, "\n\n And context is integrated : ", context.isIntegrated);
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
 * Helper to capitalize first letter
 */
function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}
