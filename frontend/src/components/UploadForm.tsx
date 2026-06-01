// frontend/src/components/UploadForm.tsx
import { useState, useEffect } from 'react';
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
  const [loadingStep, setLoadingStep] = useState(0);
  const [timeLeft, setTimeLeft] = useState(30);

  const steps = [
    "Establishing neural connection...",
    "Fetching platform metadata...",
    "Extracting audio transcripts...",
    "Processing semantic vectors...",
    "Calculating hook & engagement scores...",
    "Finalizing intelligence map..."
  ];

  useEffect(() => {
    let interval: any;
    if (loading) {
      setLoadingStep(0);
      setTimeLeft(30);
      interval = setInterval(() => {
        setLoadingStep(prev => (prev < steps.length - 1 ? prev + 1 : prev));
        setTimeLeft(prev => (prev > 5 ? prev - Math.floor(Math.random() * 3) - 1 : 5));
      }, 4000);
    }
    return () => clearInterval(interval);
  }, [loading]);

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
    const urls = platform === 'youtube' ? ytUrls : igUrls;
    const filtered = urls.filter(u => u.trim() !== '');
    
    if (filtered.length === 0) {
      alert(`Enter at least one ${platform === 'youtube' ? 'YouTube' : 'Instagram'} URL`);
      return;
    }

    setLoading(true);
    try {
      const data = await ingestVideos(
        platform === 'youtube' ? filtered : [],
        platform === 'instagram' ? filtered : []
      );
      onIngested(
        data.ingested.map(item => item.metadata),
        data.dataset_id
      );
    } catch (err: any) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const buttonGradient = platform === 'youtube' 
    ? 'from-red-600 to-red-800' 
    : 'from-fuchsia-600 to-purple-600';

  return (
    <div className="relative">
      <form onSubmit={handleSubmit} className="glass-card p-8 mb-8 transition-all duration-500 shadow-2xl border-white/10 group">
        {!loading ? (
          <div className="animate-fade-in">
            <div className="flex items-center gap-3 mb-6">
              <div className={`w-10 h-10 rounded-xl bg-gradient-to-tr ${buttonGradient} flex items-center justify-center text-white shadow-lg`}>
                <span className="text-xl">✨</span>
              </div>
              <h2 className="text-3xl font-black text-white tracking-tight">
                {platform === 'youtube' ? 'Analyze YouTube' : 'Analyze Instagram'}
              </h2>
            </div>

            <p className="text-white/50 mb-8 leading-relaxed">
              Input video URLs to decrypt their content DNA. We'll run semantic scoring, engagement mapping, and transcript analysis.
            </p>

            <div className="space-y-4 mb-8">
              {(platform === 'youtube' ? ytUrls : igUrls).map((url, i) => (
                <div key={i} className="flex gap-3 animate-slide-up" style={{ animationDelay: `${i * 100}ms` }}>
                  <input
                    type="url"
                    placeholder="https://..."
                    value={url}
                    onChange={(e) => {
                      const newArr = platform === 'youtube' ? [...ytUrls] : [...igUrls];
                      newArr[i] = e.target.value;
                      platform === 'youtube' ? setYtUrls(newArr) : setIgUrls(newArr);
                    }}
                    className="flex-1 bg-white/5 border border-white/10 rounded-2xl p-4 text-white placeholder:text-white/20 focus:ring-2 focus:ring-white/20 focus:border-white/30 transition-all outline-none"
                  />
                  {(platform === 'youtube' ? ytUrls.length : igUrls.length) > 1 && (
                    <button 
                      type="button" 
                      onClick={() => platform === 'youtube' ? removeYtField(i) : removeIgField(i)} 
                      className="w-14 h-14 flex items-center justify-center text-white/20 hover:text-red-400 transition-colors"
                    >
                      ✕
                    </button>
                  )}
                </div>
              ))}
              <button 
                type="button" 
                onClick={platform === 'youtube' ? addYtField : addIgField} 
                className="text-white/40 text-sm hover:text-white transition-colors flex items-center gap-2 pl-2"
              >
                + Add another URL
              </button>
            </div>

            <div className="flex items-center gap-6">
              <button
                type="submit"
                className={`bg-white text-black px-10 py-4 rounded-2xl font-bold shadow-xl hover:scale-105 active:scale-95 transition-all flex items-center gap-3`}
              >
                🚀 Start Analysis
              </button>
              <div className="text-xs text-white/20 font-medium tracking-widest uppercase">
                {platform === 'youtube' ? 'Public Videos Only' : 'Reels Supported'}
              </div>
            </div>
          </div>
        ) : (
          <div className="py-12 px-4 animate-fade-in text-center">
            <div className="relative w-24 h-24 mx-auto mb-10">
               <div className={`absolute inset-0 rounded-full border-4 border-white/10`}></div>
               <div className={`absolute inset-0 rounded-full border-4 ${platform === 'youtube' ? 'border-red-600' : 'border-fuchsia-600'} border-t-transparent animate-spin`}></div>
               <div className="absolute inset-0 flex items-center justify-center text-2xl">🧠</div>
            </div>

            <h3 className="text-2xl font-bold mb-2 text-glow">{steps[loadingStep]}</h3>
            <p className="text-white/40 text-sm mb-8 font-medium italic">
              Estimated time remaining: ~{timeLeft}s
            </p>

            <div className="max-w-md mx-auto">
              <div className="w-full bg-white/5 h-2 rounded-full overflow-hidden mb-6 border border-white/10">
                <div 
                  className={`h-full transition-all duration-1000 ease-out shadow-[0_0_20px_rgba(255,255,255,0.3)] ${platform === 'youtube' ? 'bg-red-600' : 'bg-gradient-to-r from-fuchsia-600 to-purple-600'}`}
                  style={{ width: `${((loadingStep + 1) / steps.length) * 100}%` }}
                ></div>
              </div>
              
              <div className="grid grid-cols-6 gap-2">
                {steps.map((_, i) => (
                  <div 
                    key={i} 
                    className={`h-1 rounded-full transition-colors duration-500 ${i <= loadingStep ? (platform === 'youtube' ? 'bg-red-600' : 'bg-fuchsia-600') : 'bg-white/5'}`}
                  ></div>
                ))}
              </div>
            </div>
            
            <p className="mt-12 text-xs text-white/20 font-bold tracking-[0.2em] uppercase">
              Processing Large Language Model Vectors
            </p>
          </div>
        )}
      </form>
    </div>
  );
}
