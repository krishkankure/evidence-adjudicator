import { FlaskConical } from 'lucide-react';

export function Header() {
  return (
    <header className="sticky top-0 z-20 border-b border-slate-200/80 bg-background/95 backdrop-blur">
      <div className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between px-4 sm:px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-md border border-slate-200 bg-white text-slate-700">
            <FlaskConical className="h-4 w-4" />
          </div>
          <div>
            <p className="text-sm font-semibold tracking-tight text-slate-900">Evidence Adjudicator</p>
            <p className="text-xs text-slate-500">Structured biomedical evidence review</p>
          </div>
        </div>
        <p className="text-xs font-medium text-slate-500">MVP · Biomedical evidence UI</p>
      </div>
    </header>
  );
}
