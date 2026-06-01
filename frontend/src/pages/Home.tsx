import { useState, useCallback, useEffect, useRef } from 'react';
import UploadForm from '../components/UploadForm';
import VideoCard from '../components/VideoCard';
import ChatSidebar from '../components/ChatSidebar';
import AnalyticsPreview from '../components/AnalyticsPreview';
import SemanticTimeline from '../components/SemanticTimeline';
import CrossPlatformComparison from '../components/CrossPlatformComparison';
import type { VideoMetadata } from '../types';

export default function Home() {
  const [activeVideos, setActiveVideos] = useState<VideoMetadata[]>([]);
  const [currentDatasetId, setCurrentDatasetId] = useState<string | null>(null);
  const [chatOpen, setChatOpen] = useState(false);
  const [chatSessionId, setChatSessionId] = useState(`session-${Date.now()}`);
  const particleContainerRef = useRef<HTMLDivElement>(null);

  // Unified Particle System
  useEffect(() => {
    const container = particleContainerRef.current;
    if (!container) return;
    const particles: any[] = [];
    const particleCount = 40;
    // Mix of YouTube Red and Instagram Purple
    const colors = ['#ef4444', '#a855f7', '#ffffff', '#3b82f6'];
    
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
        return { el: p, x, y, vx: (Math.random() - 0.5) * 0.5, vy: (Math.random() - 0.5) * 0.5 };
      }
    };

    for (let i = 0; i < particleCount; i++) {
      const p = createParticle(Math.random() * window.innerWidth, Math.random() * window.innerHeight);
      if (p) particles.push(p);
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

    const handleMouseMove = (e: MouseEvent) => {
      createParticle(e.clientX, e.clientY, true);
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('mousemove', handleMouseMove);
      container.innerHTML = '';
    };
  }, []);

  const handleIngested = useCallback((vids: VideoMetadata[], datasetId: string) => {
    setActiveVideos(prev => {
      const existingIds = new Set(prev.map(v => v.video_id));
      const uniqueNew = vids.filter(v => !existingIds.has(v.video_id));
      return [...prev, ...uniqueNew];
    });
    setCurrentDatasetId(datasetId);
    setChatOpen(true);
  }, []);

  const handleWipeMemory = useCallback(() => {
    setChatSessionId(`session-${Date.now()}`);
  }, []);

  return (
    <div className="relative min-h-screen text-white selection:bg-white/20">
      {/* Unified Background Matrix */}
      <div className="bg-video-container">
        <div className="absolute inset-0 opacity-100">
           <div className="absolute inset-0 bg-gradient-to-br from-indigo-900/40 via-black to-black"></div>
           <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?auto=format&fit=crop&q=80&w=2000')] bg-cover bg-center blur-3xl scale-110 opacity-30 mix-blend-overlay"></div>
        </div>
        <div className="bg-video-overlay"></div>
      </div>

      <div ref={particleContainerRef} className="fixed inset-0 pointer-events-none z-0"></div>

      <div className="relative z-10 flex h-screen overflow-hidden">
        <div className="flex-1 overflow-y-auto px-6 py-12 md:px-12 scroll-smooth">
          
          <header className="flex justify-between items-center mb-16 animate-fade-in">
             <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-white/10 backdrop-blur-md border border-white/20 flex items-center justify-center font-bold text-xl text-glow shadow-[0_0_15px_rgba(255,255,255,0.2)]">C</div>
                <h1 className="text-3xl font-black tracking-tight text-glow bg-gradient-to-r from-white to-white/60 bg-clip-text text-transparent">
                  CompiSmart
                </h1>
             </div>
          </header>

          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-16 animate-slide-up">
              <h2 className="text-6xl md:text-8xl font-black mb-6 tracking-tighter leading-none">
                Decrypt content <span className="bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400 bg-clip-text text-transparent italic">DNA</span>
              </h2>
              <p className="text-xl text-white/50 max-w-2xl mx-auto leading-relaxed">
                Harness production semantic models and multi-platform distribution maps for complete strategic comparison across YouTube and Instagram.
              </p>
            </div>

            {/* Context Submission Layer */}
            <div className="animate-slide-up" style={{ animationDelay: '200ms' }}>
              <UploadForm onIngested={handleIngested} />
            </div>

            {/* Integrated Multi Platform Audit Board */}
            {currentDatasetId && (
              <div className="mt-16">
                <CrossPlatformComparison datasetId={currentDatasetId} />
              </div>
            )}

            {/* Fallback Onboarding State Display */}
            {!currentDatasetId && activeVideos.length === 0 && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-12 animate-fade-in" style={{ animationDelay: '400ms' }}>
                <div className="glass-card p-10 group hover:bg-white/10 border-white/5">
                  <h3 className="text-2xl font-bold mb-4">True Cross-Platform Context</h3>
                  <p className="text-white/50 leading-relaxed">
                    Paste YouTube links and Instagram Reels into the same batch. The system automatically normalizes the metrics, letting you pit long-form content directly against short-form virality.
                  </p>
                </div>
                <div className="glass-card p-10 group hover:bg-white/10 border-white/5">
                  <h3 className="text-2xl font-bold mb-4">Target Matrix Metrics</h3>
                  <div className="space-y-3 mt-4">
                    {["Compare YouTube vs Instagram Engagement", "Benchmark Transcript Hook Scores", "Audit Multi-Platform Retention"].map(tip => (
                      <div key={tip} className="px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-sm text-white/60 italic">
                        "{tip}"
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Context Processing Dashboard Views */}
            {currentDatasetId && (
              <div className="space-y-12 py-12 animate-slide-up">
                <AnalyticsPreview platform="youtube" datasetId={currentDatasetId} />
                <SemanticTimeline datasetId={currentDatasetId} />
              </div>
            )}

            {/* Current Active Library Cards Grid */}
            {activeVideos.length > 0 && (
              <div className="py-12 animate-fade-in">
                <div className="flex justify-between items-end mb-8">
                  <div>
                    <h2 className="text-4xl font-black tracking-tight">Active Dataset Library</h2>
                    <p className="text-white/40 mt-2">Currently analyzing {activeVideos.length} mixed media assets.</p>
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                  {activeVideos.map((v, index) => (
                    <div key={`${v.platform}-${v.video_id}-${index}`} className="animate-slide-up" style={{ animationDelay: `${index * 100}ms` }}>
                      <VideoCard data={v} />
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <footer className="mt-24 pb-12 text-center text-white/20 text-xs font-medium tracking-widest uppercase">
            CompiSmart Neural Engine &copy; 2026
          </footer>
        </div>

        {/* Floating Analyzer Conversation Controller */}
        {!chatOpen && (
          <button
            onClick={() => setChatOpen(true)}
            className="fixed bottom-10 right-10 z-50 p-6 rounded-[2.5rem] bg-white text-black shadow-2xl hover:scale-110 active:scale-95 transition-all duration-500 group overflow-hidden"
          >
            <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 bg-gradient-to-br from-blue-600 to-indigo-600"></div>
            <div className="relative flex items-center gap-3 font-bold group-hover:text-white transition-colors">
              <span className="pr-2">Open Intelligence Chat</span>
            </div>
          </button>
        )}

        <ChatSidebar
          sessionId={chatSessionId}
          platform="cross-platform"
          datasetId={currentDatasetId}
          isOpen={chatOpen}
          onClose={() => setChatOpen(false)}
          onWipeMemory={handleWipeMemory}
        />
      </div>
    </div>
  );
}