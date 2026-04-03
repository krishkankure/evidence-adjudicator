'use client';

import { useCallback, useMemo, useState } from 'react';

import { adjudicateClaim, createClaim, getAdjudication } from '@/lib/api';
import { type ChatMessage } from '@/lib/types';

const LOADING_COPY = [
  'Searching the literature',
  'Comparing supporting and opposing evidence',
  'Synthesizing a structured conclusion',
];

export function useEvidenceChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runFlow = useCallback(async (prompt: string) => {
    const loadingId = crypto.randomUUID();

    setMessages((prev) => [
      ...prev,
      { id: crypto.randomUUID(), role: 'user', text: prompt },
      { id: loadingId, role: 'assistant_loading', text: 'Reviewing evidence…' },
    ]);
    setIsLoading(true);
    setError(null);

    try {
      const claim = await createClaim(prompt);
      const adjudicationRef = await adjudicateClaim(claim.claim_id);
      const adjudication = await getAdjudication(adjudicationRef.adjudication_id);

      setMessages((prev) =>
        prev.map((message) =>
          message.id === loadingId
            ? { id: crypto.randomUUID(), role: 'assistant_result', adjudication }
            : message,
        ),
      );
    } catch (error) {
      const reason = error instanceof Error ? error.message : 'Unknown failure';
      const friendly = `Unable to complete adjudication right now. Please try again.\n\nReason: ${reason}`;
      setError(friendly);
      setMessages((prev) =>
        prev.map((message) =>
          message.id === loadingId
            ? { id: crypto.randomUUID(), role: 'assistant_error', text: friendly, prompt }
            : message,
        ),
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  const submitPrompt = useCallback(
    async (prompt: string) => {
      if (!prompt.trim() || isLoading) return;
      await runFlow(prompt.trim());
    },
    [isLoading, runFlow],
  );

  const retry = useCallback(
    async (prompt: string) => {
      await submitPrompt(prompt);
    },
    [submitPrompt],
  );

  return useMemo(
    () => ({ messages, isLoading, error, submitPrompt, retry, loadingCopy: LOADING_COPY }),
    [messages, isLoading, error, submitPrompt, retry],
  );
}
