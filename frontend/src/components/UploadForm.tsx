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
    <form onSubmit={handleSubmit} className="bg-white p-6 rounded-xl shadow mb-6">
      <h2 className="text-xl font-semibold mb-4">
        {platform === 'youtube' ? 'Add YouTube Videos' : 'Add Instagram Reels'}
      </h2>

      {platform === 'youtube' && (
        <div className="mb-4">
          {ytUrls.map((url, i) => (
            <div key={i} className="flex gap-2 mt-1">
              <input
                type="url"
                placeholder="https://www.youtube.com/watch?v=..."
                value={url}
                onChange={(e) => {
                  const newArr = [...ytUrls];
                  newArr[i] = e.target.value;
                  setYtUrls(newArr);
                }}
                className="border p-2 rounded flex-1"
              />
              {ytUrls.length > 1 && (
                <button type="button" onClick={() => removeYtField(i)} className="text-red-500 font-bold">×</button>
              )}
            </div>
          ))}
          <button type="button" onClick={addYtField} className="text-blue-600 text-sm mt-1">+ Add YouTube URL</button>
        </div>
      )}

      {platform === 'instagram' && (
        <div className="mb-4">
          {igUrls.map((url, i) => (
            <div key={i} className="flex gap-2 mt-1">
              <input
                type="url"
                placeholder="https://www.instagram.com/reel/..."
                value={url}
                onChange={(e) => {
                  const newArr = [...igUrls];
                  newArr[i] = e.target.value;
                  setIgUrls(newArr);
                }}
                className="border p-2 rounded flex-1"
              />
              {igUrls.length > 1 && (
                <button type="button" onClick={() => removeIgField(i)} className="text-red-500 font-bold">×</button>
              )}
            </div>
          ))}
          <button type="button" onClick={addIgField} className="text-blue-600 text-sm mt-1">+ Add Instagram URL</button>
        </div>
      )}

      <button
        type="submit"
        disabled={loading}
        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
      >
        {loading ? 'Analyzing...' : 'Analyze Videos'}
      </button>
    </form>
  );
}