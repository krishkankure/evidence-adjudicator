import { AlertTriangle } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

export function ErrorState({ message, onRetry, prompt }: { message: string; onRetry: (prompt: string) => void; prompt: string }) {
  return (
    <Card className="p-4">
      <div className="flex items-start gap-3">
        <AlertTriangle className="mt-0.5 h-4 w-4 text-rose-500" />
        <div className="space-y-3">
          <p className="text-sm text-slate-700">{message}</p>
          <Button variant="outline" size="sm" onClick={() => onRetry(prompt)}>
            Retry
          </Button>
        </div>
      </div>
    </Card>
  );
}
