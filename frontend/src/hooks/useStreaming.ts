import { useState, useCallback } from 'react';
import { chatStream } from '../services/api';

export function useStreaming(sessionId: string) {
  const [tokens, setTokens] = useState<string[]>([]);
  const [sources, setSources] = useState<{ video_id: string; chunk_id: number | null }[]>([]);
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(
    async (question: string) => {
      setTokens([]);
      setSources([]);
      setStreaming(true);
      setError(null);

      await chatStream(
        sessionId,
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
    [sessionId]
  );

  const combinedAnswer = tokens.join('');

  return { answer: combinedAnswer, sources, streaming, error, sendMessage };
}