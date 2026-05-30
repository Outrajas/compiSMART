// frontend/src/hooks/useStreaming.ts
import { useState, useCallback } from 'react';
import { chatStream } from '../services/api';

export function useStreaming(sessionId: string, platform: string, datasetId: string | null) {
  const [tokens, setTokens] = useState<string[]>([]);
  const [sources, setSources] = useState<string[]>([]);
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(
    async (question: string) => {
      if (!datasetId) return;
      setTokens([]);
      setSources([]);
      setStreaming(true);
      setError(null);

      await chatStream(
        sessionId,
        platform,
        datasetId,
        question,
        (token) => setTokens((prev) => [...prev, token]),
        (srcs) => setSources(srcs),
        () => setStreaming(false),
        (err) => {
          setError(err);
          setStreaming(false);
        }
      );
    },
    [sessionId, platform, datasetId]
  );

  const combinedAnswer = tokens.join('');

  return { answer: combinedAnswer, sources, streaming, error, sendMessage };
}