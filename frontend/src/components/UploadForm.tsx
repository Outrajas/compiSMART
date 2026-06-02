import { useState } from 'react';
import { ingestVideos } from '../services/api'; // <--- Force through centralized secured API
import type { VideoMetadata } from '../types';

interface Props {
  onIngested: (videos: VideoMetadata[], datasetId: string) => void;
}

export default function UploadForm({ onIngested }: Props) {
  const [ytUrls, setYtUrls] = useState<string[]>(['']);
  const [igUrls, setIgUrls] = useState<string[]>(['']);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const addYtField = () => setYtUrls([...ytUrls, '']);
  const removeYtField = (index: number) => {
    if (ytUrls.length > 1) setYtUrls(ytUrls.filter((_, i) => i !== index));
  };

  const addIgField = () => setIgUrls([...igUrls, '']);
  const removeIgField = (index: number) => {
    if (igUrls.length > 1) setIgUrls(igUrls.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    const filteredYt = ytUrls.map(u => u.trim()).filter(u => u !== '');
    const filteredIg = igUrls.map(u => u.trim()).filter(u => u !== '');

    if (filteredYt.length === 0 && filteredIg.length === 0) {
      setError("Please input at least one valid YouTube or Instagram URL.");
      return;
    }

    setLoading(true);
    try {
      // Replaced the raw 401 unauthenticated fetch with our secured wrapper
      const data = await ingestVideos(filteredYt, filteredIg);
      
      const processedVideos = data.ingested.map((item: any) => ({
        video_id: item.video_id,
        platform: item.platform,
        title: item.title || item.metadata?.title,
        creator: item.creator || item.metadata?.creator,
        views: item.views || item.metadata?.views || 0,
        likes: item.likes || item.metadata?.likes || 0,
        comments: item.comments || item.metadata?.comments || 0,
        duration: item.duration || item.metadata?.duration || 0,
        follower_count: item.follower_count || item.metadata?.follower_count || 0,
        engagement_rate: item.engagement_rate || item.metadata?.engagement_rate || 0,
        hashtags: item.hashtags || item.metadata?.hashtags || []
      }));

      onIngested(processedVideos, data.dataset_id);
      setYtUrls(['']);
      setIgUrls(['']);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-8 animate-fade-in">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        
        {/* YouTube Container Card */}
        <div className="glass-card p-6 rounded-3xl bg-white/5 border border-red-500/20 shadow-[0_0_50px_-12px_rgba(220,38,38,0.15)] flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-red-600/20 border border-red-500/30 flex items-center justify-center text-red-500 font-bold font-mono">YT</div>
              <div>
                <h3 className="text-xl font-black tracking-tight text-white">YouTube Content Streams</h3>
                <p className="text-xs text-white/40">Long-form and standard algorithmic video metrics.</p>
              </div>
            </div>
            
            <div className="space-y-3 max-h-64 overflow-y-auto pr-1">
              {ytUrls.map((url, i) => (
                <div key={`yt-${i}`} className="flex gap-2 items-center">
                  <input
                    type="url"
                    placeholder="https://www.youtube.com/watch?v=..."
                    value={url}
                    onChange={(e) => {
                      const updated = [...ytUrls];
                      updated[i] = e.target.value;
                      setYtUrls(updated);
                    }}
                    className="flex-1 bg-black/40 border border-white/10 rounded-xl p-3 text-sm text-white placeholder-white/20 focus:ring-1 focus:ring-red-500 focus:outline-none"
                    disabled={loading}
                  />
                  {ytUrls.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeYtField(i)}
                      className="p-3 text-white/30 hover:text-red-400 transition"
                    >
                      ✕
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
          
          <button
            type="button"
            onClick={addYtField}
            className="text-xs font-semibold text-red-400/70 hover:text-red-400 mt-4 transition text-left pl-1"
            disabled={loading}
          >
            + Add another YouTube URL
          </button>
        </div>

        {/* Instagram Container Card */}
        <div className="glass-card p-6 rounded-3xl bg-white/5 border border-purple-500/20 shadow-[0_0_50px_-12px_rgba(168,85,247,0.15)] flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-purple-600/20 border border-purple-500/30 flex items-center justify-center text-purple-400 font-bold font-mono">IG</div>
              <div>
                <h3 className="text-xl font-black tracking-tight text-white">Instagram Reel Content</h3>
                <p className="text-xs text-white/40">Short-form engagement mapping and native subtitles.</p>
              </div>
            </div>

            <div className="space-y-3 max-h-64 overflow-y-auto pr-1">
              {igUrls.map((url, i) => (
                <div key={`ig-${i}`} className="flex gap-2 items-center">
                  <input
                    type="url"
                    placeholder="https://www.instagram.com/reel/..."
                    value={url}
                    onChange={(e) => {
                      const updated = [...igUrls];
                      updated[i] = e.target.value;
                      setIgUrls(updated);
                    }}
                    className="flex-1 bg-black/40 border border-white/10 rounded-xl p-3 text-sm text-white placeholder-white/20 focus:ring-1 focus:ring-purple-500 focus:outline-none"
                    disabled={loading}
                  />
                  {igUrls.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeIgField(i)}
                      className="p-3 text-white/30 hover:text-purple-400 transition"
                    >
                      ✕
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          <button
            type="button"
            onClick={addIgField}
            className="text-xs font-semibold text-purple-400/70 hover:text-purple-400 mt-4 transition text-left pl-1"
            disabled={loading}
          >
            + Add another Instagram URL
          </button>
        </div>

      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-400 px-4 py-3 rounded-xl text-sm font-medium">
          {error}
        </div>
      )}

      <button
        type="submit"
        disabled={loading}
        className={`w-full py-4 rounded-xl font-black text-lg transition-all duration-300 ${
          loading 
            ? 'bg-white/5 text-white/20 cursor-not-allowed'
            : 'bg-white text-black hover:scale-[1.01] active:scale-95 shadow-xl shadow-black/20'
        }`}
      >
        {loading ? "Decrypting Dynamic Cross Platform DNA..." : "Launch Consolidated Dataset Analysis"}
      </button>
    </form>
  );
}