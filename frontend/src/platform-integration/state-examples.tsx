/**
 * Example demonstrating dual-context state management
 * This shows how the same code works in both standalone and integrated modes
 */

import { useSelector } from 'react-redux';
import { 
  selectUser, 
  selectSelectedInstitution,
  selectUserContextAware,
  selectSelectedInstitutionContextAware 
} from '@/platform/v1/auth';

// Example 1: Using original selectors (will work in standalone, break in integrated)
export function ExampleComponentOriginal() {
  const user = useSelector(selectUser);
  const institution = useSelector(selectSelectedInstitution);
  
  return (
    <div>
      <h1>User: {user?.fullname}</h1>
      <p>Institution: {institution?.institution_name}</p>
    </div>
  );
}

// Example 2: Using context-aware selectors (works in both modes)
export function ExampleComponentContextAware() {
  const user = useSelector(selectUserContextAware);
  const institution = useSelector(selectSelectedInstitutionContextAware);
  
  return (
    <div>
      <h1>User: {user?.fullname}</h1>
      <p>Institution: {institution?.institution_name}</p>
    </div>
  );
}

// Example 3: Using the store adapter directly
import { useModuleSelector } from '@/platform-integration/store-adapter';

export function ExampleComponentAdapter() {
  const user = useModuleSelector('auth', (authState) => authState?.user?.value);
  const institution = useModuleSelector('auth', (authState) => authState?.selectedInstitution?.value);
  
  return (
    <div>
      <h1>User: {user?.fullname}</h1>
      <p>Institution: {institution?.institution_name}</p>
    </div>
  );
}

/**
 * Store Structure Comparison:
 * 
 * STANDALONE MODE:
 * {
 *   auth: { user: {...}, selectedInstitution: {...} },
 *   miscellaneous: { sideBarOpened: true },
 *   redirects: {...},
 *   notifications: {...}
 * }
 * 
 * INTEGRATED MODE:
 * {
 *   hostAuth: {...},
 *   hostSettings: {...},
 *   taskManagementAuth: { user: {...}, selectedInstitution: {...} },
 *   taskManagementMisc: { sideBarOpened: true },
 *   taskManagementRedirects: {...},
 *   taskManagementNotifications: {...}
 * }
 * 
 * The context-aware selectors automatically handle this difference!
 */
