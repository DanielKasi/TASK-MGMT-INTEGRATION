// Example: Refactoring imports to use Platform API
// This shows how to update existing components to use the platform API

// ❌ BEFORE (Direct imports)
/*
import { Button } from "@/platform/v1/components";
import { Badge } from "@/platform/v1/components";
import { Textarea } from "@/platform/v1/components";
import { Label } from "@/platform/v1/components";
import { selectUser } from "@/store/auth/selectors-context-aware";
import { formatTransactionDate } from "@/lib/helpers";
import apiRequest from "@/lib/apiRequest";
*/

// ✅ AFTER (Platform API imports)
import { 
  Button, 
  Badge, 
  Textarea, 
  Label 
} from "@/platform/v1/components";
import { 
  selectUser 
} from "@/platform/v1/auth";
import { 
  formatTransactionDate 
} from "@/platform/v1/utils";
import { 
  apiRequest 
} from "@/platform/v1/api";

// Example component using platform API
import { useSelector } from 'react-redux';

export function ExampleComponent() {
  const user = useSelector(selectUser);
  
  const handleAction = async () => {
    try {
      const response = await apiRequest.post('/api/example', { 
        userId: user?.id 
      });
      
      console.log('Action completed:', response);
    } catch (error) {
      console.error('Action failed:', error);
    }
  };

  return (
    <div className="space-y-4">
      <Label>User: {user?.fullname}</Label>
      <Textarea placeholder="Enter your message..." />
      <div className="flex gap-2">
        <Button onClick={handleAction}>
          Submit
        </Button>
        <Badge variant="secondary">
          {formatTransactionDate(new Date())}
        </Badge>
      </div>
    </div>
  );
}
