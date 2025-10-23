# Task Management Module

This is a modular Next.js application that can run standalone or be integrated into a host platform.

## Module Structure

```
src/
├── app/                          # Core application routes (SYNCED to host)
│   ├── (main_app)/
│   │   ├── (auth)/
│   │   └── (dashboard)/
│   ├── layout.tsx
│   ├── page.tsx
│   └── providers.tsx
├── platform/
│   └── v1/                       # Platform API surface
│       ├── auth/
│       ├── api/
│       ├── components/
│       ├── config/
│       ├── types/
│       └── utils/
├── platform-integration/         # Integration contracts (SYNCED)
│   ├── module-descriptor.ts
│   └── navigation.ts
├── store/                        # Redux store (SYNCED)
├── components/                   # UI components (SYNCED)
├── lib/                          # Utilities (SYNCED)
└── types/                        # TypeScript types (SYNCED)
```

## Development

### Standalone Mode
```bash
npm run dev
```
The app runs at `http://localhost:3000` with all routes accessible directly.

### Module Integration
This module can be integrated into a host platform using the sync script:

```bash
node scripts/sync-module.mjs \
  --repo "https://github.com/yourorg/task-management-module" \
  --tag "v1.0.0" \
  --name "tasks"
```

## Module Configuration

- **Mount Path**: `/tasks` (configurable in `module.json`)
- **Platform Version**: `>=1.0.0 <2.0.0`
- **Routes**: Dashboard, Projects, Admin, Auth pages

## Platform API Usage

Use the platform API instead of direct imports:

```typescript
// ✅ Correct
import { Button } from '@/platform/v1/components';
import { apiRequest } from '@/platform/v1/api';
import { hasPermission } from '@/platform/v1/auth';

// ❌ Avoid
import { Button } from '@/components/ui/button';
import apiRequest from '@/lib/apiRequest';
```

## Navigation

Use the navigation utilities for dual-life routing:

```typescript
import { buildModulePath } from '@/platform-integration/navigation';

// This works in both standalone and embedded contexts
const dashboardPath = buildModulePath('/dashboard');
// Standalone: '/dashboard'
// Embedded: '/tasks/dashboard'
```

## Module Descriptor

The module descriptor defines how this module integrates with the host:

- **Redux Slices**: Auth, miscellaneous, redirects, notifications
- **Sagas**: Auth and miscellaneous sagas
- **Routes**: All application routes
- **Peer Dependencies**: React, Next.js, Redux, etc.

## Building for Production

```bash
npm run build
```

The build output can be used in both standalone and embedded contexts.
