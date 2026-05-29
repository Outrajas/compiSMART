import { useState } from 'react';
import { ingestVideos } from '../services/api';
import type { VideoMetadata } from '../types';

interface Props {
  onIngested: (ytMeta: VideoMetadata, igMeta: VideoMetadata) => void;
}

export default function UploadForm({ onIngested }: Props) {
  const [ytUrl, setYtUrl] = useState('');
  const [igUrl, setIgUrl] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const data = await ingestVideos(ytUrl, igUrl);
      onIngested(data.youtube, data.instagram);
    } catch (err: any) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white p-6 rounded-xl shadow mb-6">
      <h2 className="text-xl font-semibold mb-4">Analyze Videos</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <input
          type="url"
          placeholder="YouTube URL"
          value={ytUrl}
          onChange={(e) => setYtUrl(e.target.value)}
          required
          className="border p-2 rounded w-full"
        />
        <input
          type="url"
          placeholder="Instagram Reel URL"
          value={igUrl}
          onChange={(e) => setIgUrl(e.target.value)}
          required
          className="border p-2 rounded w-full"
        />
      </div>
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