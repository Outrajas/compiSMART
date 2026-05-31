// frontend/src/components/AnalyticsPreview.tsx
import { useEffect, useState } from 'react';
import { getAnalyticsSummary, getAnalyticsRankings, getSemanticProfiles } from '../services/api';
import type { AnalyticsSummary, VideoAnalytics, SemanticProfile } from '../types';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface Props {
  platform: string;
  datasetId: string;
}

export default function AnalyticsPreview({ platform, datasetId }: Props) {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [rankings, setRankings] = useState<VideoAnalytics[]>([]);
  const [profiles, setProfiles] = useState<SemanticProfile[]>([]);

  useEffect(() => {
    getAnalyticsSummary(datasetId).then(setSummary);
    getAnalyticsRankings(datasetId).then(setRankings);
    getSemanticProfiles(datasetId).then(setProfiles);
  }, [datasetId]);

  if (!summary || summary.count === 0) return null;

  const chartData = rankings.map(v => ({
    name: v.title?.substring(0, 25) || v.video_id,
    engagement: v.engagement_rate
  }));

  const hookChartData = profiles.map(p => ({
    name: p.title?.substring(0, 25) || p.video_id,
    hookScore: p.hook_score
  }));

  const coverageData = profiles.map(p => ({
    name: p.title?.substring(0, 25) || p.video_id,
    coverage: p.transcript_coverage
  }));

  const vpfData = rankings.map(v => ({
    name: v.title?.substring(0, 25) || v.video_id,
    vpf: v.views_per_follower || 0
  }));

  const breakdownRows = profiles.map(p => ({
    title: p.title?.substring(0, 30) || p.video_id,
    ...p.hook_breakdown
  }));

  return (
    <div className="mb-8 space-y-6 animate-fade-in">
      <h2 className="text-2xl font-bold bg-gradient-to-r from-gray-800 to-gray-600 bg-clip-text text-transparent">Analytics Snapshot</h2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="glass-card p-4 text-center transition-all hover:shadow-xl">
          <div className="text-xs text-gray-500 uppercase tracking-wider">Videos</div>
          <div className="text-3xl font-extrabold text-indigo-700">{summary.count}</div>
        </div>
        <div className="glass-card p-4 text-center transition-all hover:shadow-xl">
          <div className="text-xs text-gray-500 uppercase tracking-wider">Best Engagement</div>
          <div className="text-2xl font-bold text-amber-600">{summary.best_engagement_value}%</div>
          <div className="text-xs truncate text-gray-500">{summary.best_engagement}</div>
        </div>
        <div className="glass-card p-4 text-center transition-all hover:shadow-xl">
          <div className="text-xs text-gray-500 uppercase tracking-wider">Most Views</div>
          <div className="text-2xl font-bold text-emerald-600">{summary.most_views_value?.toLocaleString()}</div>
          <div className="text-xs truncate text-gray-500">{summary.most_views_title}</div>
        </div>
        <div className="glass-card p-4 text-center transition-all hover:shadow-xl">
          <div className="text-xs text-gray-500 uppercase tracking-wider">Avg Engagement</div>
          <div className="text-2xl font-bold text-purple-600">{summary.average_engagement}%</div>
        </div>
      </div>

      {summary.outlier_videos && summary.outlier_videos.length > 0 && (
        <div className="bg-gradient-to-r from-yellow-50 to-amber-50 border-l-4 border-yellow-400 rounded-xl p-3 text-sm text-yellow-800 shadow-sm">
          ⚡ Viral outlier (extremely high Views/Follower): {summary.outlier_videos.join(', ')}
        </div>
      )}

      {chartData.length > 1 && (
        <div className="glass-card p-5 transition-all hover:shadow-md">
          <h3 className="text-md font-semibold mb-3 flex items-center gap-2">📊 Engagement Comparison</h3>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="name" tick={{fontSize: 10}} angle={-20} textAnchor="end" height={60} />
              <YAxis unit="%" />
              <Tooltip contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 25px -5px rgba(0,0,0,0.1)' }} />
              <Bar dataKey="engagement" fill="#8b5cf6" radius={[6,6,0,0]} name="Engagement %" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {vpfData.length > 1 && (
        <div className="glass-card p-5 transition-all hover:shadow-md">
          <h3 className="text-md font-semibold mb-3 flex items-center gap-2">📈 Views per Follower</h3>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={vpfData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="name" tick={{fontSize: 10}} angle={-20} textAnchor="end" height={60} />
              <YAxis />
              <Tooltip contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 25px -5px rgba(0,0,0,0.1)' }} />
              <Bar dataKey="vpf" fill="#ec4899" radius={[6,6,0,0]} name="Views/Follower" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {hookChartData.length > 0 && (
        <div className="glass-card p-5 transition-all hover:shadow-md">
          <h3 className="text-md font-semibold mb-3 flex items-center gap-2">🎣 Hook Scores (0-10)</h3>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={hookChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="name" tick={{fontSize: 10}} angle={-20} textAnchor="end" height={60} />
              <YAxis domain={[0, 10]} />
              <Tooltip contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 25px -5px rgba(0,0,0,0.1)' }} />
              <Bar dataKey="hookScore" fill="#f59e0b" radius={[6,6,0,0]} name="Hook Score" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {coverageData.length > 0 && (
        <div className="glass-card p-5 transition-all hover:shadow-md">
          <h3 className="text-md font-semibold mb-3 flex items-center gap-2">📄 Transcript Coverage (%)</h3>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={coverageData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="name" tick={{fontSize: 10}} angle={-20} textAnchor="end" height={60} />
              <YAxis unit="%" />
              <Tooltip contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 25px -5px rgba(0,0,0,0.1)' }} />
              <Bar dataKey="coverage" fill="#06b6d4" radius={[6,6,0,0]} name="Coverage %" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {breakdownRows.length > 0 && (
        <div className="glass-card p-5 overflow-x-auto transition-all hover:shadow-md">
          <h3 className="text-md font-semibold mb-3 flex items-center gap-2">🧩 Hook Score Breakdown</h3>
          <table className="w-full text-xs">
            <thead>
              <tr className="text-left border-b border-gray-200">
                <th className="py-2">Video</th>
                <th>Question</th>
                <th>Conflict</th>
                <th>Emotion</th>
                <th>Humor</th>
                <th>Curiosity</th>
                <th>CTA</th>
               </tr>
            </thead>
            <tbody>
              {breakdownRows.map((r, i) => (
                <tr key={i} className="border-b border-gray-100 hover:bg-gray-50 transition">
                  <td className="py-2 font-medium">{r.title}</td>
                  <td>{r.question}%</td>
                  <td>{r.conflict}%</td>
                  <td>{r.emotion}/10</td>
                  <td>{r.humor}/10</td>
                  <td>{r.curiosity}/10</td>
                  <td>{r.cta}/10</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}