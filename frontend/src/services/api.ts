import type { IngestResponse, ChatResponse } from '../types';

const BASE = 'http://127.0.0.1:8000'; // Use direct URL (CORS enabled)

export async function healthCheck() {
  const res = await fetch(`${BASE}/health`);
  return res.json();
}

export async function ingestVideos(youtubeUrl: string, instagramUrl: string): Promise<IngestResponse> {
  const res = await fetch(`${BASE}/ingest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ youtube_url: youtubeUrl, instagram_url: instagramUrl }),
  });
  if (!res.ok) throw new Error(`Ingest failed: ${await res.text()}`);
  return res.json();
}

export async function chat(sessionId: string, question: string): Promise<ChatResponse> {
  const res = await fetch(`${BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, question }),
  });
  if (!res.ok) throw new Error(`Chat failed: ${await res.text()}`);
  return res.json();
}

export async function chatStream(
  sessionId: string,
  question: string,
  onToken: (token: string) => void,
  onSources: (sources: { video_id: string; chunk_id: number | null }[]) => void,
  onDone: () => void,
  onError: (err: string) => void
) {
  const res = await fetch(`${BASE}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, question }),
  });
  if (!res.ok) {
    onError(`Stream error: ${await res.text()}`);
    return;
  }

  const reader = res.body?.getReader();
  const decoder = new TextDecoder();
  if (!reader) return;

  let buffer = '';
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    // Keep last incomplete line in buffer
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6);
        try {
          const parsed = JSON.parse(data);
          switch (parsed.type) {
            case 'token':
              onToken(parsed.content);
              break;
            case 'sources':
              onSources(parsed.sources);
              break;
            case 'done':
              onDone();
              break;
            case 'error':
              onError(parsed.content);
              break;
          }
        } catch {
          // ignore parse errors for incomplete lines
        }
      }
    }
  }
}