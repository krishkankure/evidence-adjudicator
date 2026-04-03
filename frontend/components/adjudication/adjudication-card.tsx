import { CitationList } from '@/components/adjudication/citation-list';
import { ConfidenceBadge } from '@/components/adjudication/confidence-badge';
import { EvidenceSection } from '@/components/adjudication/evidence-section';
import { QueryBreakdown } from '@/components/adjudication/query-breakdown';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { type AdjudicationResponse } from '@/lib/types';

function TextBlock({ label, value }: { label: string; value?: string }) {
  if (!value) return null;
  return (
    <div className="space-y-1">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
      <p className="text-sm leading-relaxed text-slate-700">{value}</p>
    </div>
  );
}

export function AdjudicationCard({ adjudication }: { adjudication: AdjudicationResponse }) {
  return (
    <Card className="overflow-hidden">
      <CardHeader className="space-y-3 bg-slate-50/50">
        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Best-supported conclusion</p>
        <CardTitle className="text-xl leading-snug">{adjudication.best_supported_conclusion}</CardTitle>
        <ConfidenceBadge confidence={adjudication.confidence} />
      </CardHeader>

      <CardContent className="space-y-6">
        <div className="grid gap-4">
          <TextBlock label="Supporting case" value={adjudication.supporting_case} />
          <TextBlock label="Opposing case" value={adjudication.opposing_case} />
          <TextBlock label="Alternative explanations" value={adjudication.alternative_explanations} />
        </div>

        <Separator />

        <section className="space-y-3">
          <h3 className="text-sm font-semibold text-slate-900">Evidence</h3>
          <EvidenceSection evidence={adjudication.evidence} />
        </section>

        <Separator />

        <section className="space-y-3">
          <h3 className="text-sm font-semibold text-slate-900">Citations</h3>
          <CitationList citations={adjudication.citations} />
        </section>

        <QueryBreakdown querySet={adjudication.query_set} />
      </CardContent>
    </Card>
  );
}
