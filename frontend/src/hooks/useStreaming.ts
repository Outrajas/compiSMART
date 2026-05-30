import { useState, useCallback, useRef, useEffect } from 'react';
import { chatStream } from '../services/api';

export function useStreaming(sessionId: string, platform: string, datasetId: string | null) {
  const [tokens, setTokens] = useState<string[]>([]);
  const [sources, setSources] = useState<string[]>([]);
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const datasetRef = useRef(datasetId);   // always current

  useEffect(() => {
    datasetRef.current = datasetId;
  }, [datasetId]);

  const sendMessage = useCallback(
    async (question: string) => {
      const currentDataset = datasetRef.current;
      if (!currentDataset) return;
      setTokens([]);
      setSources([]);
      setStreaming(true);
      setError(null);

      await chatStream(
        sessionId,
        platform,
        currentDataset,
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
    [sessionId, platform]   // datasetId is read via ref to avoid stale closures
  );

  const resetStreaming = useCallback(() => {
    setTokens([]);
    setSources([]);
    setStreaming(false);
    setError(null);
  }, []);

  const combinedAnswer = tokens.join('');

  return { answer: combinedAnswer, sources, streaming, error, sendMessage, resetStreaming };
}