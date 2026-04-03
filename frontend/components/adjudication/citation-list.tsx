import { ExternalLink } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { type Citation } from '@/lib/types';

export function CitationList({ citations }: { citations: Citation[] }) {
  if (citations.length === 0) {
    return <p className="text-sm text-slate-500">No citations were returned.</p>;
  }

  return (
    <ul className="space-y-2">
      {citations.map((citation) => (
        <li key={citation.id} className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm">
          <div className="flex items-start justify-between gap-3">
            <div className="space-y-1">
              <p className="font-medium text-slate-800">{citation.title}</p>
              <p className="text-xs text-slate-500">{[citation.journal, citation.year].filter(Boolean).join(' · ')}</p>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant={citation.branch}>{citation.branch}</Badge>
              {citation.url ? (
                <a href={citation.url} target="_blank" rel="noreferrer" className="text-slate-500 hover:text-slate-700">
                  <ExternalLink className="h-4 w-4" />
                </a>
              ) : null}
            </div>
          </div>
        </li>
      ))}
    </ul>
  );
}
