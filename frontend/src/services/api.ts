// frontend/src/services/api.ts
import type { IngestResponse, ChatResponse, AnalyticsSummary, VideoAnalytics , SemanticProfile} from '../types';

const BASE = 'http://127.0.0.1:8000';

// Volatile in-memory store for Basic Auth header token string string values
let authHeaderToken: string | null = null;

export function setApiCredentials(username: string, password: string) {
  // Compute standard RFC-7617 Basic Access Authentication string representation
  const encoded = btoa(`${username}:${password}`);
  authHeaderToken = `Basic ${encoded}`;
}

export function clearApiCredentials() {
  authHeaderToken = null;
}

function getSecuredHeaders(customHeaders: Record<string, string> = {}): Record<string, string> {
  const headers: Record<string, string> = { ...customHeaders };
  if (authHeaderToken) {
    headers['Authorization'] = authHeaderToken;
  }
  return headers;
}

export async function healthCheck() {
  const res = await fetch(`${BASE}/health`);
  return res.json();
}

export async function ingestVideos(youtubeUrls: string[], instagramUrls: string[]): Promise<IngestResponse> {
  const res = await fetch(`${BASE}/ingest`, {
    method: 'POST',
    headers: getSecuredHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ youtube_urls: youtubeUrls, instagram_urls: instagramUrls }),
  });
  if (!res.ok) throw new Error(`Ingest failed: ${await res.text()}`);
  return res.json();
}

export async function addVideoToDataset(datasetId: string, videoId: string): Promise<{ status: string; message: string }> {
  const res = await fetch(`${BASE}/analytics/dataset/add`, {
    method: 'POST',
    headers: getSecuredHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ dataset_id: datasetId, video_id: videoId }),
  });
  if (!res.ok) throw new Error(`Failed to map video to workspace: ${await res.text()}`);
  return res.json();
}

export async function removeVideoFromDataset(datasetId: string, videoId: string): Promise<{ status: string; message: string }> {
  const res = await fetch(`${BASE}/analytics/dataset/remove`, {
    method: 'POST',
    headers: getSecuredHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ dataset_id: datasetId, video_id: videoId }),
  });
  if (!res.ok) throw new Error(`Failed to isolate video from workspace: ${await res.text()}`);
  return res.json();
}

export async function chat(
  sessionId: string, 
  platform: string, 
  datasetId: string, 
  question: string,
  activeVideoIds?: string[]
): Promise<ChatResponse> {
  const res = await fetch(`${BASE}/chat`, {
    method: 'POST',
    headers: getSecuredHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ 
      session_id: sessionId, 
      platform, 
      dataset_id: datasetId, 
      question,
      active_video_ids: activeVideoIds 
    }),
  });
  if (!res.ok) throw new Error(`Chat failed: ${await res.text()}`);
  return res.json();
}

export async function chatStream(
  sessionId: string,
  platform: string,
  datasetId: string,
  question: string,
  onToken: (token: string) => void,
  onSources: (sources: string[]) => void,
  onDone: () => void,
  onError: (err: string) => void,
  activeVideoIds?: string[]
) {
  const res = await fetch(`${BASE}/chat/stream`, {
    method: 'POST',
    headers: getSecuredHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ 
      session_id: sessionId, 
      platform, 
      dataset_id: datasetId, 
      question,
      active_video_ids: activeVideoIds
    }),
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
          // ignore parse errors
        }
      }
    }
  }
}

export async function getAnalyticsSummary(datasetId: string, videoIds?: string[]): Promise<AnalyticsSummary> {
  const url = `${BASE}/analytics/summary?dataset_id=${datasetId}` + (videoIds && videoIds.length > 0 ? `&video_ids=${videoIds.join(',')}` : '');
  const res = await fetch(url, { headers: getSecuredHeaders() });
  if (!res.ok) throw new Error('Failed to fetch summary');
  return res.json();
}

export async function getAnalyticsRankings(datasetId: string, videoIds?: string[]): Promise<VideoAnalytics[]> {
  const url = `${BASE}/analytics/rankings?dataset_id=${datasetId}` + (videoIds && videoIds.length > 0 ? `&video_ids=${videoIds.join(',')}` : '');
  const res = await fetch(url, { headers: getSecuredHeaders() });
  if (!res.ok) throw new Error('Failed to fetch rankings');
  return res.json();
}

export async function getSemanticProfiles(datasetId: string, videoIds?: string[]): Promise<SemanticProfile[]> {
  const url = `${BASE}/analytics/semantic-profiles?dataset_id=${datasetId}` + (videoIds && videoIds.length > 0 ? `&video_ids=${videoIds.join(',')}` : '');
  const res = await fetch(url, { headers: getSecuredHeaders() });
  if (!res.ok) throw new Error('Failed to fetch semantic profiles');
  return res.json();
}