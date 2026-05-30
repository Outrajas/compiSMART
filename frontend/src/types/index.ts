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
  views_per_follower?: number;
  likes_per_1000_views?: number;
  comments_per_1000_views?: number;
  engagement_efficiency?: number;
}

export interface IngestedItem {
  video_id: string;
  platform: string;
  url: string;
  metadata: VideoMetadata;
  chunk_count: number;
}

export interface IngestResponse {
  dataset_id: string;
  ingested: IngestedItem[];
  status: string;
}

export interface ChatResponse {
  answer: string;
  sources: string[];
}

export interface AnalyticsSummary {
  count: number;
  total_views: number;
  total_likes: number;
  total_comments: number;
  best_engagement: string;
  best_engagement_value: number;
  most_views_title: string;
  most_views_value: number;
  most_likes_title: string;
  most_likes_value: number;
  most_comments_title: string;
  most_comments_value: number;
  largest_creator: string;
  largest_creator_followers: number;
  average_engagement: number;
  outlier_videos?: string[];
  best_views_per_follower_title?: string;
  best_views_per_follower_value?: number;
}

export interface VideoAnalytics extends VideoMetadata {
  like_ratio: number;
  comment_ratio: number;
  comment_like_ratio: number;
  follower_view_ratio: number;
  rank_by_views: number;
  rank_by_engagement: number;
  rank_by_likes: number;
  rank_by_comments: number;
}
export interface SSEEvent {
  type: 'token' | 'sources' | 'done' | 'error';
  content?: string;
  sources?: string[];
}
export interface SemanticProfile {
  video_id: string;
  title: string;
  hook_score: number;
  avg_humor: number;
  avg_curiosity: number;
  avg_emotion: number;
  avg_conflict: number;
  avg_question: number;
  avg_cta: number;
  transcript_coverage: number;
  total_segments: number;
  hook_breakdown: {
    question: number;
    conflict: number;
    emotion: number;
    humor: number;
    curiosity: number;
    cta: number;
  };
}