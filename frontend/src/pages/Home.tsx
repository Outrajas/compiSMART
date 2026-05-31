// frontend/src/pages/Home.tsx
import { useState, useCallback } from 'react';
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
  const [chatSessionId, setChatSessionId] = useState(`session-${Date.now()}`);

  const currentVideos = platform === 'youtube' ? youtubeVideos : instagramVideos;
  const currentDatasetId = platform === 'youtube' ? youtubeDatasetId : instagramDatasetId;

  const handleIngested = useCallback((platformName: string, vids: VideoMetadata[], datasetId: string) => {
    if (platformName === 'youtube') {
      setYoutubeVideos(prev => {
        const existingIds = new Set(prev.map(v => v.video_id));
        const uniqueNew = vids.filter(v => !existingIds.has(v.video_id));
        return [...prev, ...uniqueNew];
      });
      setYoutubeDatasetId(datasetId);
    } else {
      setInstagramVideos(prev => {
        const existingIds = new Set(prev.map(v => v.video_id));
        const uniqueNew = vids.filter(v => !existingIds.has(v.video_id));
        return [...prev, ...uniqueNew];
      });
      setInstagramDatasetId(datasetId);
    }
    setChatOpen(true);
  }, []);

  const handleWipeMemory = useCallback(() => {
    setChatSessionId(`session-${Date.now()}`);
  }, []);

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Main content */}
      <div className="flex-1 overflow-y-auto p-6 md:p-8">
        <h1 className="text-4xl font-extrabold text-center mb-8 bg-gradient-to-r from-indigo-700 via-purple-700 to-pink-600 bg-clip-text text-transparent drop-shadow-sm animate-fade-in">
          Creator Analytics Studio
        </h1>

        {/* Platform tabs */}
        <div className="flex justify-center mb-8 space-x-4">
          <button
            onClick={() => setPlatform('youtube')}
            className={`px-8 py-2.5 rounded-full font-semibold transition-all duration-200 transform hover:scale-105 ${
              platform === 'youtube'
                ? 'bg-gradient-to-r from-red-500 to-red-700 text-white shadow-md shadow-red-200'
                : 'bg-gray-100/80 backdrop-blur-sm text-gray-700 hover:bg-gray-200'
            }`}
          >
            YouTube
          </button>
          <button
            onClick={() => setPlatform('instagram')}
            className={`px-8 py-2.5 rounded-full font-semibold transition-all duration-200 transform hover:scale-105 ${
              platform === 'instagram'
                ? 'bg-gradient-to-r from-pink-500 to-rose-600 text-white shadow-md shadow-pink-200'
                : 'bg-gray-100/80 backdrop-blur-sm text-gray-700 hover:bg-gray-200'
            }`}
          >
            Instagram
          </button>
        </div>

        <UploadForm
          platform={platform}
          onIngested={(vids, datasetId) => handleIngested(platform, vids, datasetId)}
          allowedPlatform={platform}
        />

        {currentDatasetId && (
          <div className="animate-slide-up">
            <AnalyticsPreview platform={platform} datasetId={currentDatasetId} />
            <SemanticTimeline datasetId={currentDatasetId} />
          </div>
        )}

        {currentVideos.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            {currentVideos.map((v, index) => (
              <div key={`${v.platform}-${v.video_id}-${index}`} className="animate-fade-in" style={{ animationDelay: `${index * 50}ms` }}>
                <VideoCard data={v} />
              </div>
            ))}
          </div>
        )}
      </div>

      {!chatOpen && (
        <button
          onClick={() => setChatOpen(true)}
          className="fixed bottom-6 right-6 z-50 bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-4 rounded-full shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:scale-110 hover:rotate-3"
          title="Toggle AI Chat"
        >
          💬
        </button>
      )}

      <ChatSidebar
        sessionId={chatSessionId}
        platform={platform}
        datasetId={currentDatasetId}
        isOpen={chatOpen}
        onClose={() => setChatOpen(false)}
        onWipeMemory={handleWipeMemory}
      />
    </div>
  );
}