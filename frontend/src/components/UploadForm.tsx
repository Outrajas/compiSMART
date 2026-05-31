// frontend/src/components/UploadForm.tsx
import { useState } from 'react';
import { ingestVideos } from '../services/api';
import type { VideoMetadata } from '../types';

interface Props {
  platform: 'youtube' | 'instagram';
  onIngested: (videos: VideoMetadata[], datasetId: string) => void;
  allowedPlatform: 'youtube' | 'instagram';
}

export default function UploadForm({ platform, onIngested }: Props) {
  const [ytUrls, setYtUrls] = useState<string[]>(['']);
  const [igUrls, setIgUrls] = useState<string[]>(['']);
  const [loading, setLoading] = useState(false);

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
    if (platform === 'youtube') {
      const filtered = ytUrls.filter(u => u.trim() !== '');
      if (filtered.length === 0) {
        alert('Enter at least one YouTube URL');
        return;
      }
      setLoading(true);
      try {
        const data = await ingestVideos(filtered, []);
        onIngested(
          data.ingested.map(item => item.metadata),
          data.dataset_id
        );
      } catch (err: any) {
        alert(err.message);
      } finally {
        setLoading(false);
      }
    } else {
      const filtered = igUrls.filter(u => u.trim() !== '');
      if (filtered.length === 0) {
        alert('Enter at least one Instagram URL');
        return;
      }
      setLoading(true);
      try {
        const data = await ingestVideos([], filtered);
        onIngested(
          data.ingested.map(item => item.metadata),
          data.dataset_id
        );
      } catch (err: any) {
        alert(err.message);
      } finally {
        setLoading(false);
      }
    }
  };

  return (
    <form onSubmit={handleSubmit} className="glass-card p-6 mb-8 transition-all duration-300">
      <h2 className="text-2xl font-bold mb-5 bg-gradient-to-r from-gray-800 to-gray-600 bg-clip-text text-transparent">
        {platform === 'youtube' ? 'Add YouTube Videos' : 'Add Instagram Reels'}
      </h2>

      {platform === 'youtube' && (
        <div className="mb-5">
          {ytUrls.map((url, i) => (
            <div key={i} className="flex gap-2 mt-2">
              <input
                type="url"
                placeholder="https://www.youtube.com/watch?v=..."
                value={url}
                onChange={(e) => {
                  const newArr = [...ytUrls];
                  newArr[i] = e.target.value;
                  setYtUrls(newArr);
                }}
                className="border border-gray-200 rounded-xl p-3 flex-1 focus:ring-2 focus:ring-red-400 focus:border-transparent transition-all shadow-sm"
              />
              {ytUrls.length > 1 && (
                <button type="button" onClick={() => removeYtField(i)} className="text-red-500 font-bold text-xl hover:scale-110 transition">×</button>
              )}
            </div>
          ))}
          <button type="button" onClick={addYtField} className="text-red-500 text-sm mt-2 hover:underline flex items-center gap-1">+ Add YouTube URL</button>
        </div>
      )}

      {platform === 'instagram' && (
        <div className="mb-5">
          {igUrls.map((url, i) => (
            <div key={i} className="flex gap-2 mt-2">
              <input
                type="url"
                placeholder="https://www.instagram.com/reel/..."
                value={url}
                onChange={(e) => {
                  const newArr = [...igUrls];
                  newArr[i] = e.target.value;
                  setIgUrls(newArr);
                }}
                className="border border-gray-200 rounded-xl p-3 flex-1 focus:ring-2 focus:ring-pink-400 focus:border-transparent transition-all shadow-sm"
              />
              {igUrls.length > 1 && (
                <button type="button" onClick={() => removeIgField(i)} className="text-red-500 font-bold text-xl hover:scale-110 transition">×</button>
              )}
            </div>
          ))}
          <button type="button" onClick={addIgField} className="text-pink-500 text-sm mt-2 hover:underline flex items-center gap-1">+ Add Instagram URL</button>
        </div>
      )}

      <button
        type="submit"
        disabled={loading}
        className="mt-4 bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-6 py-3 rounded-xl font-semibold shadow-md hover:shadow-xl transition-all duration-200 transform hover:scale-[1.02] disabled:opacity-50 disabled:hover:scale-100"
      >
        {loading ? (
          <span className="flex items-center gap-2">
            <svg className="animate-spin h-5 w-5 text-white" viewBox="0 0 24 24">...</svg>
            Analyzing...
          </span>
        ) : (
          'Analyze Videos ✨'
        )}
      </button>
    </form>
  );
}