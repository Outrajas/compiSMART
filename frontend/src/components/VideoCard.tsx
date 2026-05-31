// frontend/src/components/VideoCard.tsx
import type { VideoMetadata } from '../types';

export default function VideoCard({ data }: { data: VideoMetadata }) {
  if (!data || Object.keys(data).length === 0) return null;

  return (
    <div className="group bg-white/90 backdrop-blur-sm rounded-2xl shadow-md hover:shadow-2xl transition-all duration-300 hover:-translate-y-1 border border-gray-100 overflow-hidden">
      <div className="p-5">
        <h3 className="font-bold text-lg mb-3 line-clamp-2 group-hover:text-indigo-700 transition-colors">
          {data.title || `Video ${data.video_id}`}
        </h3>
        <ul className="space-y-2 text-sm">
          <li className="flex justify-between"><span className="font-medium text-gray-500">Creator:</span> <span>{data.creator || 'N/A'}</span></li>
          <li className="flex justify-between"><span className="font-medium text-gray-500">Views:</span> <span>{data.views?.toLocaleString()}</span></li>
          <li className="flex justify-between"><span className="font-medium text-gray-500">Likes:</span> <span>{data.likes?.toLocaleString()}</span></li>
          <li className="flex justify-between"><span className="font-medium text-gray-500">Comments:</span> <span>{data.comments?.toLocaleString()}</span></li>
          <li className="flex justify-between"><span className="font-medium text-gray-500">Followers:</span> <span>{data.follower_count?.toLocaleString() || 'N/A'}</span></li>
          <li className="flex justify-between"><span className="font-medium text-gray-500">Duration:</span> <span>{data.duration ? `${data.duration}s` : 'N/A'}</span></li>
          <li className="flex justify-between"><span className="font-medium text-gray-500">Engagement:</span> <span className="font-mono">{data.engagement_rate != null ? `${data.engagement_rate.toFixed(4)}%` : 'N/A'}</span></li>
          <li><span className="font-medium text-gray-500">Hashtags:</span> <div className="flex flex-wrap gap-1 mt-1">{data.hashtags?.slice(0,3).map(t => <span key={t} className="text-xs bg-gray-100 px-2 py-0.5 rounded-full">#{t}</span>)}{data.hashtags?.length > 3 && <span className="text-xs">+{data.hashtags.length-3}</span>}</div></li>
        </ul>
      </div>
    </div>
  );
}