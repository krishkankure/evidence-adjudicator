import { ExternalLink } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { type EvidenceCard as EvidenceCardType } from '@/lib/types';

export function EvidenceCard({ item }: { item: EvidenceCardType }) {
  return (
    <Card className="p-4">
      <div className="space-y-2">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-sm font-medium text-slate-900">{item.title}</p>
            <p className="text-xs text-slate-500">
              {[item.journal, item.year].filter(Boolean).join(' · ') || 'Journal metadata unavailable'}
            </p>
          </div>
          <Badge variant={item.branch}>{item.branch}</Badge>
        </div>

        {item.snippet ? <p className="text-sm leading-relaxed text-slate-600">{item.snippet}</p> : null}

        <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500">
          {item.pmid ? <span>PMID {item.pmid}</span> : null}
          {item.url ? (
            <a href={item.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 hover:text-slate-700">
              Source <ExternalLink className="h-3.5 w-3.5" />
            </a>
          ) : null}
        </div>
      </div>
    </Card>
  );
}
