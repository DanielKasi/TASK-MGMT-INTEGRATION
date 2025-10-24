// Re-export API client from existing lib
export { default as apiRequest } from '@/lib/apiRequest';

// Additional API utilities can be added here
export const buildApiUrl = (endpoint: string, baseUrl?: string): string => {
  const base = baseUrl ?? process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
  return `${base}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
};
