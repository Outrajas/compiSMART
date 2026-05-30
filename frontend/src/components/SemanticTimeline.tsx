import { useEffect, useState } from 'react';
import { getSemanticProfiles } from '../services/api';
import type { SemanticProfile } from '../types';

interface Props {
  datasetId: string;
}

export default function SemanticTimeline({ datasetId }: Props) {
  const [profiles, setProfiles] = useState<SemanticProfile[]>([]);

  useEffect(() => {
    getSemanticProfiles(datasetId).then(setProfiles);
  }, [datasetId]);

  if (profiles.length === 0) return null;

  return (
    <div className="bg-white p-4 rounded-lg shadow mb-6">
      <h3 className="text-sm font-medium mb-3">📈 Semantic Strength by Video</h3>
      <div className="space-y-3">
        {profiles.map(p => (
          <div key={p.video_id}>
            <div className="flex justify-between text-xs mb-1">
              <span className="font-medium truncate w-2/3">{p.title}</span>
              <span>Hook {p.hook_score}/10</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div className="bg-amber-500 h-2 rounded-full" style={{ width: `${p.hook_score * 10}%` }}></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}