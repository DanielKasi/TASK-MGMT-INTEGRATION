// Module path utilities for dual-life modules
// This handles routing in both standalone and embedded contexts

export interface ModulePathConfig {
  mountPath: string;
  isStandalone: boolean;
}

// Default configuration - can be overridden by host
let pathConfig: ModulePathConfig = {
  mountPath: '/tasks',
  isStandalone: true,
};

export const setModulePathConfig = (config: ModulePathConfig) => {
  pathConfig = config;
};

export const getModulePathConfig = (): ModulePathConfig => pathConfig;

/**
 * Builds a module path that works in both standalone and embedded contexts
 * @param path - The internal route path (e.g., '/dashboard')
 * @returns The full path (e.g., '/tasks/dashboard' in host, '/dashboard' in standalone)
 */
export const buildModulePath = (path: string): string => {
  if (pathConfig.isStandalone) {
    return path;
  }
  
  // Ensure path starts with /
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  
  // Ensure mountPath doesn't end with /
  const normalizedMountPath = pathConfig.mountPath.endsWith('/') 
    ? pathConfig.mountPath.slice(0, -1) 
    : pathConfig.mountPath;
  
  return `${normalizedMountPath}${normalizedPath}`;
};

/**
 * Builds multiple module paths at once
 * @param paths - Array of internal route paths
 * @returns Array of full paths
 */
export const buildModulePaths = (paths: string[]): string[] => {
  return paths.map(buildModulePath);
};

/**
 * Extracts the internal path from a full module path
 * @param fullPath - The full path (e.g., '/tasks/dashboard')
 * @returns The internal path (e.g., '/dashboard')
 */
export const extractInternalPath = (fullPath: string): string => {
  if (pathConfig.isStandalone) {
    return fullPath;
  }
  
  const normalizedMountPath = pathConfig.mountPath.endsWith('/') 
    ? pathConfig.mountPath.slice(0, -1) 
    : pathConfig.mountPath;
  
  if (fullPath.startsWith(normalizedMountPath)) {
    const internalPath = fullPath.slice(normalizedMountPath.length);
    return internalPath || '/';
  }
  
  return fullPath;
};

/**
 * Checks if a path belongs to this module
 * @param path - The path to check
 * @returns True if the path belongs to this module
 */
export const isModulePath = (path: string): boolean => {
  if (pathConfig.isStandalone) {
    return true; // In standalone mode, all paths belong to the module
  }
  
  const normalizedMountPath = pathConfig.mountPath.endsWith('/') 
    ? pathConfig.mountPath.slice(0, -1) 
    : pathConfig.mountPath;
  
  return path.startsWith(normalizedMountPath);
};
