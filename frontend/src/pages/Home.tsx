import { useState } from 'react';
import UploadForm from '../components/UploadForm';
import VideoCard from '../components/VideoCard';
import ChatSidebar from '../components/ChatSidebar';
import AnalyticsPreview from '../components/AnalyticsPreview';
import SemanticTimeline from '../components/SemanticTimeline';
import type { VideoMetadata } from '../types';

export default function Home() {
  const [platform, setPlatform] = useState<'youtube' | 'instagram'>('youtube');
  const [youtubeVideos, setYoutubeVideos] = useState<VideoMetadata[]>([]);
  const [instagramVideos, setInstagramVideos] = useState<VideoMetadata[]>([]);
  const [youtubeDatasetId, setYoutubeDatasetId] = useState<string | null>(null);
  const [instagramDatasetId, setInstagramDatasetId] = useState<string | null>(null);
  const [chatOpen, setChatOpen] = useState(false);

  const currentVideos = platform === 'youtube' ? youtubeVideos : instagramVideos;
  const currentDatasetId = platform === 'youtube' ? youtubeDatasetId : instagramDatasetId;

  const handleIngested = (platformName: string, vids: VideoMetadata[], datasetId: string) => {
    if (platformName === 'youtube') {
      setYoutubeVideos(prev => [...prev, ...vids.filter(v => !prev.find(p => p.video_id === v.video_id))]);
      setYoutubeDatasetId(datasetId);
    } else {
      setInstagramVideos(prev => [...prev, ...vids.filter(v => !prev.find(p => p.video_id === v.video_id))]);
      setInstagramDatasetId(datasetId);
    }
    setChatOpen(true);
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <div className="flex-1 overflow-y-auto p-4">
        <h1 className="text-3xl font-bold text-center mb-8">Creator Analytics Studio</h1>

        <div className="flex justify-center mb-6 space-x-4">
          <button onClick={() => setPlatform('youtube')} className={`px-6 py-2 rounded-full font-medium ${platform === 'youtube' ? 'bg-red-600 text-white' : 'bg-gray-200 text-gray-700'}`}>YouTube</button>
          <button onClick={() => setPlatform('instagram')} className={`px-6 py-2 rounded-full font-medium ${platform === 'instagram' ? 'bg-pink-600 text-white' : 'bg-gray-200 text-gray-700'}`}>Instagram</button>
        </div>

        <UploadForm
          platform={platform}
          onIngested={(vids, datasetId) => handleIngested(platform, vids, datasetId)}
          allowedPlatform={platform}
        />

        {currentDatasetId && (
          <>
            <AnalyticsPreview platform={platform} datasetId={currentDatasetId} />
            <SemanticTimeline datasetId={currentDatasetId} />
          </>
        )}

        {currentVideos.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
            {currentVideos.map(v => <VideoCard key={v.video_id} data={v} />)}
          </div>
        )}
      </div>

      <ChatSidebar
        sessionId={`demo-${platform}`}
        platform={platform}
        datasetId={currentDatasetId}
        isOpen={chatOpen}
        onClose={() => setChatOpen(false)}
      />
    </div>
  );
}