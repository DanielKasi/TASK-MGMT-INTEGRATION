
import { useRouter } from 'next/navigation';
import { useMemo } from 'react';
import { buildModulePath } from '@/platform/v1/utils/routing';

export function useModuleNavigation() {
  const router = useRouter();
  
  const navigation = useMemo(() => ({
    ...router,
    push: (route: string) => {
      router.push(buildModulePath(route));
    },
    replace: (route: string) => {
      router.replace(buildModulePath(route));
    },
    
  }), [router]);
  
  return navigation;
}
