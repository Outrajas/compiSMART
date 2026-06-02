import type { VideoMetadata } from '../types';

interface Props {
  data: VideoMetadata;
  isActive: boolean;
  onToggleActive: () => void;
}

export default function VideoCard({ data, isActive, onToggleActive }: Props) {
  const isYoutube = data.platform.toLowerCase() === 'youtube';
  const views = data.views || 0;
  const engagement = data.engagement_rate || 0;

  return (
    <div className={`glass-card overflow-hidden group hover:border-white/20 transition-all duration-500 bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-6 flex flex-col justify-between h-full space-y-6 ${
      !isActive ? 'opacity-40 saturate-50 scale-[0.98] border-dashed border-white/5' : ''
    }`}>
      <div>
        <div className="flex justify-between items-center gap-4 mb-4">
          <span className={`px-3 py-1 rounded-full text-xs font-mono font-bold tracking-wider uppercase ${
            isYoutube ? 'bg-red-500/20 text-red-400' : 'bg-purple-500/20 text-purple-400'
          }`}>
            {data.platform}
          </span>
          <button 
            type="button"
            onClick={onToggleActive}
            className={`text-xs px-2.5 py-1 rounded-lg font-bold font-mono transition-all duration-300 ${
              isActive 
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 hover:bg-rose-500/20 hover:text-rose-400 hover:border-rose-500/30' 
                : 'bg-white/10 text-white/40 border border-white/10 hover:bg-emerald-500/20 hover:text-emerald-400'
            }`}
          >
            {isActive ? "✓ CONTEXT ACTIVE" : "✕ EXCLUDED"}
          </button>
        </div>

        <h4 className="text-lg font-bold text-white group-hover:text-glow transition duration-300 line-clamp-2 mb-2" title={data.title}>
          {data.title || "Untitled Platform Asset"}
        </h4>
        <p className="text-sm text-white/60 font-medium">
          Creator: <span className="text-white font-semibold">@{data.creator || "unknown"}</span>
        </p>
      </div>

      <div className="space-y-3 pt-4 border-t border-white/5">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="block text-xs text-white/40 uppercase tracking-wider mb-0.5">Views</span>
            <span className="font-mono font-bold text-white text-base">
              {views > 0 ? views.toLocaleString() : "N/A (Blocked)"}
            </span>
          </div>
          <div>
            <span className="block text-xs text-white/40 uppercase tracking-wider mb-0.5">Engagement</span>
            <span className="font-mono font-bold text-pink-400 text-base">
              {engagement > 0 ? `${engagement.toFixed(4)}%` : "N/A"}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="block text-xs text-white/40 uppercase tracking-wider mb-0.5">Likes</span>
            <span className="font-mono text-white/80">{(data.likes || 0).toLocaleString()}</span>
          </div>
          <div>
            <span className="block text-xs text-white/40 uppercase tracking-wider mb-0.5">Comments</span>
            <span className="font-mono text-white/80">{(data.comments || 0).toLocaleString()}</span>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 text-sm pt-1">
          <div>
            <span className="block text-xs text-white/40 uppercase tracking-wider mb-0.5">Followers</span>
            <span className="font-mono text-white/50 text-xs">
              {data.follower_count && data.follower_count > 0 ? data.follower_count.toLocaleString() : "N/A (Hidden)"}
            </span>
          </div>
          <div>
            <span className="block text-xs text-white/40 uppercase tracking-wider mb-0.5">Duration</span>
            <span className="font-mono text-white/80">{Number(data.duration || 0).toFixed(1)}s</span>
          </div>
        </div>
      </div>

      {data.hashtags && data.hashtags.length > 0 && (
        <div className="flex flex-wrap gap-1.5 pt-2">
          {data.hashtags.slice(0, 3).map((tag, i) => (
            <span key={i} className="text-[11px] font-mono px-2 py-0.5 rounded bg-white/5 text-white/40">
              #{tag}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}