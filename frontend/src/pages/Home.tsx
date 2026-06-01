// frontend/src/pages/Home.tsx
import { useState, useCallback, useEffect, useRef } from 'react';
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
  const particleContainerRef = useRef<HTMLDivElement>(null);

  const currentVideos = platform === 'youtube' ? youtubeVideos : instagramVideos;
  const currentDatasetId = platform === 'youtube' ? youtubeDatasetId : instagramDatasetId;

  // Particle System & Mouse Trail
  useEffect(() => {
    const container = particleContainerRef.current;
    if (!container) return;

    const particles: HTMLDivElement[] = [];
    const particleCount = 40;
    const colors = platform === 'youtube' ? ['#ff0000', '#880000', '#ffffff'] : ['#e1306c', '#833ab4', '#ffffff'];

    const createParticle = (x: number, y: number, isTrail = false) => {
      const p = document.createElement('div');
      p.className = 'particle';
      const size = isTrail ? Math.random() * 8 + 4 : Math.random() * 5 + 2;
      p.style.width = `${size}px`;
      p.style.height = `${size}px`;
      p.style.left = `${x}px`;
      p.style.top = `${y}px`;
      p.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
      p.style.opacity = (Math.random() * 0.5 + 0.2).toString();
      
      if (isTrail) {
        p.style.transition = 'all 1s ease-out';
        container.appendChild(p);
        setTimeout(() => {
          p.style.transform = `translate(${(Math.random() - 0.5) * 100}px, ${(Math.random() - 0.5) * 100}px) scale(0)`;
          p.style.opacity = '0';
          setTimeout(() => p.remove(), 1000);
        }, 10);
      } else {
        container.appendChild(p);
        return {
          el: p,
          x,
          y,
          vx: (Math.random() - 0.5) * 0.5,
          vy: (Math.random() - 0.5) * 0.5,
        };
      }
    };

    // Ambient particles
    for (let i = 0; i < particleCount; i++) {
      const p = createParticle(Math.random() * window.innerWidth, Math.random() * window.innerHeight);
      if (p) particles.push(p as any);
    }

    const moveParticles = () => {
      particles.forEach((p: any) => {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0 || p.x > window.innerWidth) p.vx *= -1;
        if (p.y < 0 || p.y > window.innerHeight) p.vy *= -1;
        p.el.style.left = `${p.x}px`;
        p.el.style.top = `${p.y}px`;
      });
      requestAnimationFrame(moveParticles);
    };
    const animId = requestAnimationFrame(moveParticles);

    // Mouse trail
    const handleMouseMove = (e: MouseEvent) => {
      createParticle(e.clientX, e.clientY, true);
    };
    window.addEventListener('mousemove', handleMouseMove);

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('mousemove', handleMouseMove);
      container.innerHTML = '';
    };
  }, [platform]);

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
    <div className="relative min-h-screen text-white selection:bg-white/20">
      {/* Background Layer */}
      <div className="bg-video-container">
        {/* Placeholder for blurred video background */}
        <div className={`absolute inset-0 transition-opacity duration-1000 ${platform === 'youtube' ? 'opacity-100' : 'opacity-0'}`}>
           <div className="absolute inset-0 bg-gradient-to-br from-red-900/40 to-black"></div>
           <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?auto=format&fit=crop&q=80&w=2000')] bg-cover bg-center blur-3xl scale-110 opacity-40"></div>
        </div>
        <div className={`absolute inset-0 transition-opacity duration-1000 ${platform === 'instagram' ? 'opacity-100' : 'opacity-0'}`}>
           <div className="absolute inset-0 bg-gradient-to-br from-purple-900/40 to-black"></div>
           <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1611270624006-039c3664d50c?auto=format&fit=crop&q=80&w=2000')] bg-cover bg-center blur-3xl scale-110 opacity-40"></div>
        </div>
        <div className="bg-video-overlay"></div>
      </div>

      {/* Particle Layer */}
      <div ref={particleContainerRef} className="fixed inset-0 pointer-events-none z-0"></div>

      {/* Main UI */}
      <div className="relative z-10 flex h-screen overflow-hidden">
        <div className="flex-1 overflow-y-auto px-6 py-12 md:px-12 scroll-smooth">
          {/* Header */}
          <header className="flex justify-between items-center mb-16 animate-fade-in">
             <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-white/10 backdrop-blur-md border border-white/20 flex items-center justify-center font-bold text-xl text-glow">C</div>
                <h1 className="text-3xl font-black tracking-tight text-glow bg-gradient-to-r from-white to-white/60 bg-clip-text text-transparent">
                  CompiSmart
                </h1>
             </div>
             <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-white/60">
                <a href="#" className="hover:text-white transition-colors">Platform</a>
                <a href="#" className="hover:text-white transition-colors">Intelligence</a>
                <a href="#" className="hover:text-white transition-colors">Pricing</a>
             </nav>
          </header>

          <div className="max-w-6xl mx-auto">
            {/* Hero Section */}
            <div className="text-center mb-16 animate-slide-up">
              <h2 className="text-6xl md:text-8xl font-black mb-6 tracking-tighter leading-none">
                Decrypt your content's <span className="bg-gradient-to-r from-white via-white/80 to-white/40 bg-clip-text text-transparent italic">DNA</span>
              </h2>
              <p className="text-xl text-white/50 max-w-2xl mx-auto leading-relaxed">
                Harness AI-driven semantic profiles and engagement mapping for the next generation of storytelling.
              </p>
            </div>

            {/* Platform Selection */}
            <div className="flex justify-center mb-16 animate-fade-in" style={{ animationDelay: '200ms' }}>
              <div className="glass-card p-1.5 flex gap-1 bg-white/5">
                <button
                  onClick={() => setPlatform('youtube')}
                  className={`flex items-center gap-2 px-10 py-3.5 rounded-2xl font-bold transition-all duration-500 ${
                    platform === 'youtube'
                      ? 'bg-red-600 text-white shadow-[0_0_40px_-5px_rgba(220,38,38,0.5)]'
                      : 'text-white/40 hover:bg-white/5'
                  }`}
                >
                  <span className="text-xl">🎬</span> YouTube
                </button>
                <button
                  onClick={() => setPlatform('instagram')}
                  className={`flex items-center gap-2 px-10 py-3.5 rounded-2xl font-bold transition-all duration-500 ${
                    platform === 'instagram'
                      ? 'bg-gradient-to-br from-fuchsia-600 to-purple-600 text-white shadow-[0_0_40px_-5px_rgba(192,38,211,0.5)]'
                      : 'text-white/40 hover:bg-white/5'
                  }`}
                >
                  <span className="text-xl">📸</span> Instagram
                </button>
              </div>
            </div>

            {/* Upload Section */}
            <div className="animate-slide-up" style={{ animationDelay: '400ms' }}>
              <UploadForm
                platform={platform}
                onIngested={(vids, datasetId) => handleIngested(platform, vids, datasetId)}
                allowedPlatform={platform}
              />
            </div>

            {/* Empty State / Initial View */}
            {!currentDatasetId && currentVideos.length === 0 && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-12 animate-fade-in" style={{ animationDelay: '600ms' }}>
                <div className="glass-card p-10 group hover:bg-white/10 border-white/5">
                  <div className="w-16 h-16 rounded-2xl bg-white/10 flex items-center justify-center text-3xl mb-6 group-hover:scale-110 transition-transform">🚀</div>
                  <h3 className="text-2xl font-bold mb-4">Intelligence Engine</h3>
                  <p className="text-white/50 leading-relaxed">
                    Automatically score hooks, rank engagement trends, and build semantic maps from your transcripts using LLM-based analysis.
                  </p>
                </div>
                <div className="glass-card p-10 group hover:bg-white/10 border-white/5">
                  <div className="w-16 h-16 rounded-2xl bg-white/10 flex items-center justify-center text-3xl mb-6 group-hover:scale-110 transition-transform">💡</div>
                  <h3 className="text-2xl font-bold mb-4">Query Your Content</h3>
                  <div className="space-y-3 mt-6">
                    {["Which video has the best hook?", "Summarize my top performers", "What triggers virality?"].map(tip => (
                      <div key={tip} className="px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-sm text-white/60 italic">
                        "{tip}"
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Data Views */}
            {currentDatasetId && (
              <div className="space-y-12 py-12 animate-slide-up">
                <AnalyticsPreview platform={platform} datasetId={currentDatasetId} />
                <SemanticTimeline datasetId={currentDatasetId} />
              </div>
            )}

            {currentVideos.length > 0 && (
              <div className="py-12 animate-fade-in">
                <div className="flex justify-between items-end mb-8">
                  <div>
                    <h2 className="text-4xl font-black tracking-tight">Content Library</h2>
                    <p className="text-white/40 mt-2">Deep analysis ready for {currentVideos.length} assets</p>
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                  {currentVideos.map((v, index) => (
                    <div key={`${v.platform}-${v.video_id}-${index}`} className="animate-slide-up" style={{ animationDelay: `${index * 100}ms` }}>
                      <VideoCard data={v} />
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <footer className="mt-24 pb-12 text-center text-white/20 text-xs font-medium tracking-widest uppercase">
            CompiSmart Neural Engine &copy; 2024
          </footer>
        </div>

        {/* AI FAB Toggle */}
        {!chatOpen && (
          <button
            onClick={() => setChatOpen(true)}
            className="fixed bottom-10 right-10 z-50 p-6 rounded-[2.5rem] bg-white text-black shadow-2xl hover:scale-110 active:scale-95 transition-all duration-500 group overflow-hidden"
          >
            <div className={`absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 ${platform === 'youtube' ? 'bg-red-600' : 'bg-gradient-to-br from-fuchsia-600 to-purple-600'}`}></div>
            <div className="relative flex items-center gap-3 font-bold group-hover:text-white transition-colors">
              <span className="text-2xl">💬</span>
              <span className="pr-2">CompiSmart Analyst</span>
            </div>
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
    </div>
  );
}