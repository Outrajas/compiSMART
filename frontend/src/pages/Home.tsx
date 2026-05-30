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

  // Called when new videos are ingested
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

  // Wipe memory: generate new session id
  const handleWipeMemory = useCallback(() => {
    setChatSessionId(`session-${Date.now()}`);
  }, []);

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Main content */}
      <div className="flex-1 overflow-y-auto p-4">
        <h1 className="text-3xl font-bold text-center mb-8">Creator Analytics Studio</h1>

        {/* Platform tabs */}
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
            {currentVideos.map((v, index) => (
              <VideoCard key={`${v.platform}-${v.video_id}-${index}`} data={v} />
            ))}
          </div>
        )}
      </div>

      {!chatOpen && (
  <button 
    onClick={() => setChatOpen(true)} 
    className="fixed bottom-6 right-6 z-50 bg-blue-600 text-white p-4 rounded-full shadow-lg hover:bg-blue-700 transition" 
    title="Toggle AI Chat"
  > 
    💬 
  </button>
)}

{/* Chat sidebar */}
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