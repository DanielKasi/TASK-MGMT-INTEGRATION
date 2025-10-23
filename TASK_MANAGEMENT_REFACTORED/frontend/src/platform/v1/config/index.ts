// Platform configuration utilities
export type PlatformConfig = {
  apiBaseUrl: string;
  locale: string;
  timezone: string;
  environment: 'development' | 'staging' | 'production';
};

export const getServerConfig = (): PlatformConfig => ({
  apiBaseUrl: process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000',
  locale: process.env.NEXT_PUBLIC_LOCALE ?? 'en-US',
  timezone: process.env.NEXT_PUBLIC_TIMEZONE ?? 'UTC',
  environment: (process.env.NODE_ENV as PlatformConfig['environment']) ?? 'development',
});

export const getClientConfig = (): Omit<PlatformConfig, 'environment'> => ({
  apiBaseUrl: process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000',
  locale: process.env.NEXT_PUBLIC_LOCALE ?? 'en-US',
  timezone: process.env.NEXT_PUBLIC_TIMEZONE ?? 'UTC',
});
