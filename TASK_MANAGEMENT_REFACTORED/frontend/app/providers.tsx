import { ReduxProvider } from '@/providers/ReduxProvider';
import { NotificationsProvider } from '@/providers/notifications-provider';

export default function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ReduxProvider>
      <NotificationsProvider>
        {children}
      </NotificationsProvider>
    </ReduxProvider>
  );
}
