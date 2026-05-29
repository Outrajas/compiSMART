import type { VideoMetadata } from '../types';

export default function VideoCard({ data }: { data: VideoMetadata }) {
  if (!data || Object.keys(data).length === 0) return null;

  return (
    <div className="bg-white p-4 rounded-xl shadow border">
      <h3 className="font-bold text-lg mb-2">{data.title || `Video ${data.video_id}`}</h3>
      <ul className="space-y-1 text-sm">
        <li><span className="font-medium">Creator:</span> {data.creator || 'N/A'}</li>
        <li><span className="font-medium">Views:</span> {data.views?.toLocaleString()}</li>
        <li><span className="font-medium">Likes:</span> {data.likes?.toLocaleString()}</li>
        <li><span className="font-medium">Comments:</span> {data.comments?.toLocaleString()}</li>
        <li><span className="font-medium">Followers:</span> {data.follower_count?.toLocaleString() || 'N/A'}</li>
        <li><span className="font-medium">Duration:</span> {data.duration}s</li>
        <li><span className="font-medium">Engagement Rate:</span> {data.engagement_rate?.toFixed(4)}%</li>
        <li><span className="font-medium">Hashtags:</span> {data.hashtags?.join(', ') || 'None'}</li>
      </ul>
    </div>
  );
}