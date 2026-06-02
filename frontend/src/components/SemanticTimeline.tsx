import { useEffect, useState } from 'react';
import { getSemanticProfiles } from '../services/api';
import type { SemanticProfile } from '../types';

interface Props {
  datasetId: string;
  activeVideoIds: string[];
}

export default function SemanticTimeline({ datasetId, activeVideoIds }: Props) {
  const [profiles, setProfiles] = useState<SemanticProfile[]>([]);

  useEffect(() => {
    if (!datasetId || activeVideoIds.length === 0) {
      setProfiles([]);
      return;
    }
    getSemanticProfiles(datasetId, activeVideoIds).then(setProfiles);
  }, [datasetId, activeVideoIds]);

  if (profiles.length === 0) return null;

  return (
    <div className="glass-card p-5 mb-8 transition-all hover:shadow-md">
      <h3 className="text-md font-semibold mb-4 flex items-center gap-2 text-white">📈 Semantic Strength by Video</h3>
      <div className="space-y-4">
        {profiles.map((p, idx) => (
          <div key={p.video_id} className="animate-fade-in" style={{ animationDelay: `${idx * 80}ms` }}>
            <div className="flex justify-between text-xs mb-1">
              <span className="font-medium truncate w-2/3 text-white/90">{p.title}</span>
              <span className="font-mono font-bold text-amber-300">Hook {p.hook_score}/10</span>
            </div>
            <div className="w-full bg-white/20 rounded-full h-2.5 overflow-hidden shadow-inner">
              <div
                className="bg-gradient-to-r from-amber-400 to-orange-500 h-2.5 rounded-full transition-all duration-700 ease-out"
                style={{ width: `${p.hook_score * 10}%` }}
              ></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}