import { Sparkles } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

const EXAMPLES = [
  'Does KRAS G12C predict response to KRAS inhibitors in NSCLC?',
  'Is HER2-low associated with response to trastuzumab deruxtecan in metastatic breast cancer?',
  'Does EGFR exon 19 deletion predict response to osimertinib?',
];

export function EmptyState({ onPromptClick }: { onPromptClick: (prompt: string) => void }) {
  return (
    <Card className="mx-auto max-w-3xl p-8 sm:p-10">
      <div className="space-y-6">
        <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-600">
          <Sparkles className="h-3.5 w-3.5" />
          Structured biomedical evidence review
        </div>
        <div className="space-y-2">
          <h1 className="text-3xl font-semibold tracking-tight text-slate-900">Evidence Adjudicator</h1>
          <p className="text-sm leading-relaxed text-slate-600 sm:text-base">
            Ask a biomedical claim. The system retrieves supporting, opposing, and alternative evidence before
            returning a structured conclusion.
          </p>
        </div>
        <div className="space-y-3">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Example prompts</p>
          <div className="grid gap-2">
            {EXAMPLES.map((example) => (
              <Button
                key={example}
                variant="outline"
                className="h-auto justify-start whitespace-normal py-3 text-left text-sm font-normal text-slate-700"
                onClick={() => onPromptClick(example)}
              >
                {example}
              </Button>
            ))}
          </div>
        </div>
      </div>
    </Card>
  );
}
