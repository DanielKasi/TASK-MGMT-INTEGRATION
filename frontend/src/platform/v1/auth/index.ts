// Platform auth utilities
export { hasPermission } from '@/lib/helpers';

// Re-export auth selectors and actions
export {
  selectAccessToken,
  selectSelectedInstitution,
  selectUser,
  selectUserLoading,
  selectAttachedInstitutions,
} from '@/store/auth/selectors';

export {
  fetchRemoteUserStart,
  fetchUpToDateInstitution,
  logoutStart,
  userActivityDetected,
  clearTemporaryPermissions,
} from '@/store/auth/actions';

// Auth types
export type { IUser } from '@/types/user.types';
export type { IUserInstitution } from '@/types/other';

// Context-aware selectors for dual-mode compatibility
export {
  selectUser as selectUserContextAware,
  selectAccessToken as selectAccessTokenContextAware,
  selectSelectedInstitution as selectSelectedInstitutionContextAware,
  selectUserLoading as selectUserLoadingContextAware,
  selectAttachedInstitutions as selectAttachedInstitutionsContextAware,
} from '@/store/auth/selectors-context-aware';

// Auth utilities
export const getAuthHeaders = (token: string) => ({
  Authorization: `Bearer ${token}`,
  'Content-Type': 'application/json',
});

export const isAuthenticated = (token: string | null): boolean => {
  return !!token && token.length > 0;
};
