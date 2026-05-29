import { useState } from 'react';
import UploadForm from '../components/UploadForm';
import VideoCard from '../components/VideoCard';
import ChatWindow from '../components/ChatWindow';
import type { VideoMetadata } from '../types';

export default function Home() {
  const [ytMeta, setYtMeta] = useState<VideoMetadata | null>(null);
  const [igMeta, setIgMeta] = useState<VideoMetadata | null>(null);
  const sessionId = 'demo-session'; // Fixed for demo, can be dynamic later

  const handleIngested = (yt: VideoMetadata, ig: VideoMetadata) => {
    setYtMeta(yt);
    setIgMeta(ig);
  };

  return (
    <div className="max-w-7xl mx-auto p-4">
      <h1 className="text-3xl font-bold text-center mb-8">Video Performance Analyzer</h1>
      <UploadForm onIngested={handleIngested} />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        {ytMeta && <VideoCard data={ytMeta} />}
        {igMeta && <VideoCard data={igMeta} />}
      </div>

      <ChatWindow sessionId={sessionId} metadataA={ytMeta || undefined} metadataB={igMeta || undefined} />
    </div>
  );
}