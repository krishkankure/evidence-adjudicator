import { AdjudicationCard } from '@/components/adjudication/adjudication-card';
import { type AdjudicationResponse } from '@/lib/types';

export function AssistantMessage({ adjudication }: { adjudication: AdjudicationResponse }) {
  return <AdjudicationCard adjudication={adjudication} />;
}
