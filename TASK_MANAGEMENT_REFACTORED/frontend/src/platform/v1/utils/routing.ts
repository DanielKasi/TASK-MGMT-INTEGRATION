

/**
 * Stub for the host platform's buildModulePath that must take into account the module name and the route; See comment below for the implementation in the host platform
 * @param route - The route to build the module path for
 * @returns The module path
 */

export function buildModulePath(route: string){
    return route
  };
  
  // const MODULE_PATHS = new Map(
  //   moduleDescriptors.map(m => [m.name, m.routeBasePath])
  // );
  
  // export function buildModulePath(moduleName: string, route: string): string {
  //   const basePath = MODULE_PATHS.get(moduleName) || '';
  //   return basePath + route;
  // }
