import {
  type AdjudicateClaimResponse,
  type AdjudicationResponse,
  type BranchEnum,
  type ClaimResponse,
  type Citation,
  type ConfidenceEnum,
  type EvidenceCard,
  type QuerySet,
} from '@/lib/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || 'Request failed.');
  }

  return response.json() as Promise<T>;
}

export function createClaim(userText: string): Promise<ClaimResponse> {
  return request<ClaimResponse>('/claims', {
    method: 'POST',
    body: JSON.stringify({ user_text: userText }),
  });
}

export function adjudicateClaim(claimId: string): Promise<AdjudicateClaimResponse> {
  return request<AdjudicateClaimResponse>(`/claims/${claimId}/adjudicate`, {
    method: 'POST',
  });
}

export async function getAdjudication(adjudicationId: string): Promise<AdjudicationResponse> {
  const detail = await request<Record<string, unknown>>(`/adjudications/${adjudicationId}`);

  const adjudicationNode = asRecord(detail.adjudication);
  const evidenceNode = asRecord(detail.evidence);
  const generatedQueries = detail.generated_queries ?? evidenceNode.generated_queries;

  const acceptedEvidence = asArrayOfRecords(evidenceNode.accepted_evidence);
  const rejectedEvidence = asArrayOfRecords(evidenceNode.rejected_candidates);
  const evidenceRows = [...acceptedEvidence, ...rejectedEvidence];

  return {
    adjudication_id: String(detail.adjudication_id ?? adjudicationId),
    claim_id: String(detail.claim_id ?? ''),
    best_supported_conclusion: String(
      adjudicationNode.best_supported_conclusion ??
        detail.best_supported_conclusion ??
        detail.conclusion ??
        detail.adjudication_summary ??
        'No conclusion returned.',
    ),
    confidence: normalizeConfidence(adjudicationNode.confidence ?? detail.confidence),
    supporting_case: asOptionalString(adjudicationNode.supporting_case ?? detail.supporting_case),
    opposing_case: asOptionalString(adjudicationNode.opposing_case ?? detail.opposing_case),
    alternative_explanations: asOptionalString(
      adjudicationNode.alternative_explanations ?? detail.alternative_explanations,
    ),
    query_set: parseQuerySet(generatedQueries),
    evidence: evidenceRows.map((row, index) => mapEvidence(row, index)),
    citations: asArrayOfRecords(detail.citations).map((row, index) => mapCitation(row, index)),
  };
}

function parseQuerySet(value: unknown): QuerySet | undefined {
  const record = asRecord(value);

  if (Array.isArray(record.items)) {
    const queriesByIntent = new Map<string, string>();
    for (const item of record.items) {
      if (typeof item !== 'object' || item === null) continue;
      const queryItem = item as Record<string, unknown>;
      const intent = asOptionalString(queryItem.intent);
      const query = asOptionalString(queryItem.query);
      if (intent && query) queriesByIntent.set(intent, query);
    }

    return {
      supporting: queriesByIntent.get('direct_support') ?? queriesByIntent.get('supporting'),
      opposing: queriesByIntent.get('opposing'),
      alternative: queriesByIntent.get('alternative_contextual') ?? queriesByIntent.get('alternative'),
    };
  }

  const fallback = {
    supporting: asOptionalString(record.supporting ?? record.support_query),
    opposing: asOptionalString(record.opposing ?? record.oppose_query),
    alternative: asOptionalString(record.alternative ?? record.alternative_query),
  };

  if (!fallback.supporting && !fallback.opposing && !fallback.alternative) return undefined;
  return fallback;
}

function mapEvidence(row: Record<string, unknown>, index: number): EvidenceCard {
  const branch = normalizeBranch(row.branch ?? row.label ?? row.decision);
  const pmid = asOptionalString(row.pmid);
  return {
    id: String(row.id ?? row.evidence_id ?? `${branch}-${index}`),
    title: String(row.title ?? row.source_title ?? 'Untitled evidence'),
    journal: asOptionalString(row.journal ?? row.source_journal),
    year: asOptionalString(row.year ?? row.source_year),
    pmid,
    snippet: asOptionalString(row.snippet ?? row.extracted_snippet ?? row.finding),
    branch,
    url:
      asOptionalString(row.url ?? row.citation_link) ??
      (pmid ? `https://pubmed.ncbi.nlm.nih.gov/${pmid}/` : undefined),
  };
}

function mapCitation(row: Record<string, unknown>, index: number): Citation {
  const branch = normalizeBranch(row.branch ?? row.label);
  return {
    id: String(row.id ?? row.citation_id ?? `${branch}-citation-${index}`),
    title: String(row.title ?? row.source_title ?? 'Untitled citation'),
    journal: asOptionalString(row.journal ?? row.source_journal),
    year: asOptionalString(row.year ?? row.source_year),
    branch,
    url: asOptionalString(row.url ?? row.citation_link),
  };
}

function normalizeConfidence(value: unknown): ConfidenceEnum {
  const normalized = String(value ?? 'unknown').toLowerCase();
  if (normalized.includes('high')) return 'high';
  if (normalized.includes('medium')) return 'medium';
  if (normalized.includes('low')) return 'low';
  return 'unknown';
}

function normalizeBranch(value: unknown): BranchEnum {
  const normalized = String(value ?? '').toLowerCase();
  if (normalized.includes('opp')) return 'opposing';
  if (normalized.includes('alt')) return 'alternative';
  return 'supporting';
}

function asOptionalString(value: unknown): string | undefined {
  if (typeof value === 'string' && value.trim().length > 0) return value;
  if (typeof value === 'number') return String(value);
  return undefined;
}

function asRecord(value: unknown): Record<string, unknown> {
  if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
    return value as Record<string, unknown>;
  }
  return {};
}

function asArrayOfRecords(value: unknown): Record<string, unknown>[] {
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is Record<string, unknown> => typeof item === 'object' && item !== null);
}
