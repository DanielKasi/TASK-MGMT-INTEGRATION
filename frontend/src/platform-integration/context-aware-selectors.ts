
import { useSelector } from 'react-redux';
import { getDynamicSliceKey } from './dynamic-context-detection';

// This function creates a selector that works in both standalone and integrated modes
export function createContextAwareSelector<T>(
  sliceName: string,
  selector: (sliceState: any) => T
) {
  return (state: any): T | undefined => {
    // Get the correct slice key for the current context using dynamic detection
    const sliceKey = getDynamicSliceKey(sliceName, state);

    console.log("\n\n\n\n  sliceKey", sliceKey, "\n\n For slice name :", sliceName);
    // console.log("\n\n state[sliceKey]", state[sliceKey || ""]);
    if (sliceKey && state[sliceKey]) {
      try {
        return selector(state[sliceKey]);
      } catch (err) {
        // If selector fails, continue to fallback
      }
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
