import { Reducer, AnyAction } from '@reduxjs/toolkit';

export interface ModuleDescriptor {
  name: string;
  version: string;
  platformVersion: string;
  routeBasePath: string;
  routes: string[];
  slices: Record<string, Reducer<any, AnyAction>>;
  sagas?: Array<() => Generator>;
  rtkApis?: Array<{
    reducerPath: string;
    reducer: any;
    middleware: any;
  }>;
  peerDeps: Record<string, string>;
}

export interface PlatformConfig {
  apiBaseUrl: string;
  locale: string;
  timezone: string;
  environment: 'development' | 'staging' | 'production';
}

export interface ModuleManifest {
  name: string;
  version: string;
  platformVersion: string;
  mountPath: string;
  routes: string[];
  peerDeps: Record<string, string>;
  description?: string;
  author?: string;
}
