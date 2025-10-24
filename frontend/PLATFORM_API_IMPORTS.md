# Platform API Import Guide

## ✅ Correct Import Patterns

### UI Components
```typescript
// ✅ Correct - Import from platform components index
import { Button, Card, Badge, Separator } from "@/platform/v1/components";

// ❌ Incorrect - Don't import from individual UI paths
import { Button } from "@/platform/v1/components/ui/button";
```

### API Client
```typescript
// ✅ Correct - Import from platform API
import { apiRequest } from "@/platform/v1/api";

// ❌ Incorrect - Don't import directly from lib
import apiRequest from "@/lib/apiRequest";
```

### Utilities
```typescript
// ✅ Correct - Import from platform utils
import { cn, formatDate, formatTransactionDate } from "@/platform/v1/utils";

// ❌ Incorrect - Don't import directly from lib
import { cn } from "@/lib/utils";
```

### Auth
```typescript
// ✅ Correct - Import from platform auth
import { selectUser, hasPermission } from "@/platform/v1/auth";

// ❌ Incorrect - Don't import directly from store
import { selectUser } from "@/store/auth/selectors";
```

## 🔧 Platform API Structure

The platform API exports everything from its main index files:

```
src/platform/v1/
├── components/index.ts    # Exports all UI components
├── api/index.ts          # Exports API client
├── auth/index.ts         # Exports auth utilities
├── utils/index.ts        # Exports utility functions
└── index.ts              # Exports everything
```

## 📝 Migration Tips

1. **Import from platform index files** - Don't go deeper into subdirectories
2. **Use named imports** - `import { Button } from "@/platform/v1/components"`
3. **Keep existing imports** - Your current imports still work (backward compatible)
4. **Gradual migration** - Update imports at your own pace

## 🎯 Example Migration

```typescript
// Before
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import apiRequest from "@/lib/apiRequest";
import { cn } from "@/lib/utils";

// After
import { Button, Card } from "@/platform/v1/components";
import { apiRequest } from "@/platform/v1/api";
import { cn } from "@/platform/v1/utils";
```
