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

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? '/api';

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly path: string,
    public readonly status?: number,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${path}`;

  let response: Response;
  try {
    response = await fetch(url, {
      ...init,
      headers: {
        'Content-Type': 'application/json',
        ...(init?.headers ?? {}),
      },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Network request failed.';
    throw new ApiError(`Network error calling ${path}: ${message}`, path);
  }

  if (!response.ok) {
    const raw = await response.text();
    let parsedMessage = raw;
    try {
      const parsed = JSON.parse(raw) as { error?: { message?: string } };
      parsedMessage = parsed.error?.message ?? raw;
    } catch {
      // keep raw text
    }

    const message = parsedMessage?.trim() || `Request failed with status ${response.status}.`;
    throw new ApiError(`API ${response.status} calling ${path}: ${message}`, path, response.status);
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
  const [adjudication, evidencePayload, citationRows] = await Promise.all([
    request<Record<string, unknown>>(`/adjudications/${adjudicationId}`),
    request<Record<string, unknown> | Record<string, unknown>[]>(`/adjudications/${adjudicationId}/evidence`),
    request<Record<string, unknown>[]>(`/adjudications/${adjudicationId}/citations`),
  ]);

  const querySet = parseQuerySet(adjudication.generated_queries);

  const evidenceRows = normalizeEvidenceRows(evidencePayload);

  return {
    adjudication_id: String(adjudication.adjudication_id ?? adjudicationId),
    claim_id: String(adjudication.claim_id ?? ''),
    best_supported_conclusion: String(
      adjudication.best_supported_conclusion ??
        adjudication.conclusion ??
        adjudication.adjudication_summary ??
        'No conclusion returned.',
    ),
    confidence: normalizeConfidence(adjudication.confidence),
    supporting_case: asOptionalString(adjudication.supporting_case),
    opposing_case: asOptionalString(adjudication.opposing_case),
    alternative_explanations: asOptionalString(adjudication.alternative_explanations),
    query_set: querySet,
    evidence: evidenceRows.map((row, index) => mapEvidence(row, index)),
    citations: citationRows.map((row, index) => mapCitation(row, index)),
  };
}

function normalizeEvidenceRows(value: Record<string, unknown> | Record<string, unknown>[]): Record<string, unknown>[] {
  if (Array.isArray(value)) return value;
  const accepted = value.accepted_evidence;
  if (Array.isArray(accepted)) return accepted as Record<string, unknown>[];
  const retrieved = value.retrieved_candidates;
  if (Array.isArray(retrieved)) return retrieved as Record<string, unknown>[];
  return [];
}

function parseQuerySet(value: unknown): QuerySet | undefined {
  if (!value || typeof value !== 'object') return undefined;
  const record = value as Record<string, unknown>;
  return {
    supporting: asOptionalString(record.supporting ?? record.support_query),
    opposing: asOptionalString(record.opposing ?? record.oppose_query),
    alternative: asOptionalString(record.alternative ?? record.alternative_query),
  };
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
    url: asOptionalString(row.url ?? row.citation_link) ?? (pmid ? `https://pubmed.ncbi.nlm.nih.gov/${pmid}/` : undefined),
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
