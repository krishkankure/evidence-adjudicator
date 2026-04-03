import { EvidenceCard } from '@/components/adjudication/evidence-card';
import { type BranchEnum, type EvidenceCard as EvidenceCardType } from '@/lib/types';

const BRANCH_LABELS: Record<BranchEnum, string> = {
  supporting: 'Supporting evidence',
  opposing: 'Opposing evidence',
  alternative: 'Alternative evidence',
};

export function EvidenceSection({ evidence }: { evidence: EvidenceCardType[] }) {
  return (
    <div className="space-y-6">
      {(Object.keys(BRANCH_LABELS) as BranchEnum[]).map((branch) => {
        const items = evidence.filter((item) => item.branch === branch);
        if (items.length === 0) return null;
        return (
          <section key={branch} className="space-y-3">
            <h4 className="text-sm font-semibold text-slate-800">{BRANCH_LABELS[branch]}</h4>
            <div className="space-y-3">
              {items.map((item) => (
                <EvidenceCard key={item.id} item={item} />
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}
