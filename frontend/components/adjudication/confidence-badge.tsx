import { Badge } from '@/components/ui/badge';
import { type ConfidenceEnum } from '@/lib/types';

export function ConfidenceBadge({ confidence }: { confidence: ConfidenceEnum }) {
  return (
    <Badge variant={confidence === 'unknown' ? 'neutral' : confidence} className="capitalize">
      {confidence} confidence
    </Badge>
  );
}
