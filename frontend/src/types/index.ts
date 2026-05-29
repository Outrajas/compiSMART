export interface VideoMetadata {
  video_id: string;
  platform: string;
  title?: string;
  creator?: string;
  views?: number;
  likes?: number;
  comments?: number;
  duration?: number;
  upload_date?: string;
  hashtags?: string[];
  follower_count?: number;
  engagement_rate?: number;
}

export interface IngestResponse {
  youtube: VideoMetadata;
  instagram: VideoMetadata;
  transcript_preview: string;
  chunk_count: number;
  status: string;
}

export interface ChatResponse {
  answer: string;
  sources: { video_id: string; chunk_id: number | null }[];
}

export interface SSEEvent {
  type: 'token' | 'sources' | 'done' | 'error';
  content?: string;
  sources?: { video_id: string; chunk_id: number | null }[];
}