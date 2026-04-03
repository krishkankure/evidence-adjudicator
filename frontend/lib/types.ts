export type ConfidenceEnum = 'low' | 'medium' | 'high' | 'unknown';
export type BranchEnum = 'supporting' | 'opposing' | 'alternative';

export interface ClaimResponse {
  claim_id: string;
  user_text: string;
  created_at?: string;
}

export interface AdjudicateClaimResponse {
  adjudication_id: string;
  status?: string;
}

export interface QuerySet {
  supporting?: string;
  opposing?: string;
  alternative?: string;
}

export interface EvidenceCard {
  id: string;
  title: string;
  journal?: string;
  year?: string | number;
  pmid?: string;
  snippet?: string;
  branch: BranchEnum;
  url?: string;
}

export interface Citation {
  id: string;
  title: string;
  journal?: string;
  year?: string | number;
  branch: BranchEnum;
  url?: string;
}

export interface AdjudicationResponse {
  adjudication_id: string;
  claim_id: string;
  best_supported_conclusion: string;
  confidence: ConfidenceEnum;
  supporting_case?: string;
  opposing_case?: string;
  alternative_explanations?: string;
  query_set?: QuerySet;
  evidence: EvidenceCard[];
  citations: Citation[];
}

export type ChatMessage =
  | { id: string; role: 'user'; text: string }
  | { id: string; role: 'assistant_loading'; text: string }
  | { id: string; role: 'assistant_result'; adjudication: AdjudicationResponse }
  | { id: string; role: 'assistant_error'; text: string; prompt: string };
