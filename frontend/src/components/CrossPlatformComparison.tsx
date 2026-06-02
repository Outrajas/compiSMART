import { useEffect, useState } from 'react';
import { getAnalyticsRankings, getSemanticProfiles } from '../services/api';
import type { VideoAnalytics, SemanticProfile } from '../types';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface Props {
  datasetId: string;
  activeVideoIds: string[];
}

export default function CrossPlatformComparison({ datasetId, activeVideoIds }: Props) {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function loadCrossPlatformData() {
      if (!datasetId || activeVideoIds.length === 0) {
        setData([]);
        return;
      }
      setLoading(true);
      try {
        const rankings = await getAnalyticsRankings(datasetId, activeVideoIds);
        const profiles = await getSemanticProfiles(datasetId, activeVideoIds);

        const formatted = rankings.map((item: VideoAnalytics) => {
          const profileMatch = profiles.find(p => p.video_id === item.video_id);
          return {
            id: item.video_id,
            title: item.title || `Asset ${item.video_id}`,
            platform: item.platform.toUpperCase(),
            engagement: item.engagement_rate || 0,
            hookScore: profileMatch ? profileMatch.hook_score : 0,
            views: item.views || 0,
            creator: item.creator || 'Unknown'
          };
        });

        setData(formatted);
      } catch (err) {
        console.error("Error generating cross platform matrix data:", err);
      } finally {
        setLoading(false);
      }
    }

    loadCrossPlatformData();
  }, [datasetId, activeVideoIds]);

  if (data.length === 0) return null;

  return (
    <div className="glass-card p-6 md:p-8 mb-12 border-white/10 shadow-2xl animate-fade-in bg-white/5 backdrop-blur-xl rounded-3xl">
      <div className="mb-6">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-widest bg-gradient-to-r from-blue-500/20 to-indigo-500/20 border border-white/10 mb-3">
          📊 Benchmark Matrix
        </div>
        <h3 className="text-3xl font-black tracking-tight text-glow bg-gradient-to-r from-white to-white/60 bg-clip-text text-transparent">
          Cross-Platform Performance Audit
        </h3>
        <p className="text-sm text-white/50 mt-1">
          Directly comparing YouTube vs Instagram content DNA based on engagement efficiency and hook anchors.
        </p>
      </div>

      {loading ? (
        <div className="py-12 text-center text-white/40 font-mono animate-pulse">Recalibrating dataset metrics...</div>
      ) : (
        <div className="space-y-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="bg-white/5 border border-white/5 rounded-2xl p-4">
              <h4 className="text-sm font-bold uppercase tracking-wider text-white/70 mb-4">Engagement Rate Comparison</h4>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                  <XAxis dataKey="title" tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 10 }} tickFormatter={(val) => val.substring(0, 15) + '...'} />
                  <YAxis unit="%" tick={{ fill: 'rgba(255,255,255,0.6)' }} />
                  <Tooltip contentStyle={{ backgroundColor: '#111', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.2)', color: '#fff' }} />
                  <Bar dataKey="engagement" radius={[4, 4, 0, 0]} name="Engagement Rate %">
                    {data.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.platform === 'YOUTUBE' ? '#ef4444' : '#a855f7'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="bg-white/5 border border-white/5 rounded-2xl p-4">
              <h4 className="text-sm font-bold uppercase tracking-wider text-white/70 mb-4">Transcript Hook Strength (0-10)</h4>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                  <XAxis dataKey="title" tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 10 }} tickFormatter={(val) => val.substring(0, 15) + '...'} />
                  <YAxis domain={[0, 10]} tick={{ fill: 'rgba(255,255,255,0.6)' }} />
                  <Tooltip contentStyle={{ backgroundColor: '#111', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.2)', color: '#fff' }} />
                  <Bar dataKey="hookScore" radius={[4, 4, 0, 0]} name="Hook Score">
                     {data.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.platform === 'YOUTUBE' ? '#fca5a5' : '#d8b4fe'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="overflow-x-auto border border-white/10 rounded-2xl">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="bg-white/10 text-xs uppercase tracking-wider text-white/60 border-b border-white/10">
                <tr>
                  <th className="p-4">Platform</th>
                  <th className="p-4">Title / Identifier</th>
                  <th className="p-4">Creator Node</th>
                  <th className="p-4 text-right">Views</th>
                  <th className="p-4 text-right">Engagement Rate</th>
                  <th className="p-4 text-right">Hook Power</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {data.map((row, idx) => (
                  <tr key={idx} className="hover:bg-white/5 transition">
                    <td className="p-4 font-mono font-bold">
                      <span className={`px-2.5 py-1 rounded-md text-xs ${row.platform === 'YOUTUBE' ? 'bg-red-500/20 text-red-400' : 'bg-purple-500/20 text-purple-400'}`}>
                        {row.platform}
                      </span>
                    </td>
                    <td className="p-4 font-medium max-w-xs truncate text-white" title={row.title}>{row.title}</td>
                    <td className="p-4 text-white/70">@{row.creator}</td>
                    <td className="p-4 text-right font-mono text-white/60">{row.views.toLocaleString()}</td>
                    <td className="p-4 text-right font-mono text-blue-400 font-bold">{row.engagement.toFixed(4)}%</td>
                    <td className="p-4 text-right font-mono text-amber-400 font-bold">{row.hookScore}/10</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}