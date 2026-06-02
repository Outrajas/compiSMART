import { useEffect, useState } from 'react';
import { getAnalyticsRankings, getAnalyticsSummary } from '../services/api';
import type { VideoAnalytics, AnalyticsSummary } from '../types';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface Props {
  platform: 'youtube' | 'instagram';
  datasetId: string;
  activeVideoIds: string[];
}

export default function AnalyticsPreview({ platform, datasetId, activeVideoIds }: Props) {
  const [rankings, setRankings] = useState<VideoAnalytics[]>([]);
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadAnalytics() {
      if (!datasetId || activeVideoIds.length === 0) {
        setRankings([]);
        setSummary(null);
        setLoading(false);
        return;
      }
      setLoading(true);
      try {
        const rData = await getAnalyticsRankings(datasetId, activeVideoIds);
        const sData = await getAnalyticsSummary(datasetId, activeVideoIds);
        setRankings(rData);
        setSummary(sData);
      } catch (err) {
        console.error("Error retrieving analytics preview structure:", err);
      } finally {
        setLoading(false);
      }
    }
    loadAnalytics();
  }, [datasetId, platform, activeVideoIds]);

  if (loading) return <div className="py-12 text-center text-white/40 font-mono animate-pulse">Computing audit visualizations...</div>;
  if (rankings.length === 0) return null;

  const hasFollowerData = rankings.some(r => r.follower_count && r.follower_count > 0);
  const themeColor = platform === 'youtube' ? '#dc2626' : '#c084fc';

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="glass-card p-6 bg-white/5 border border-white/10 rounded-2xl">
          <span className="text-xs text-white/40 uppercase tracking-widest font-mono">Analyzed Content</span>
          <div className="text-3xl font-black mt-1">{rankings.length} Assets</div>
        </div>
        <div className="glass-card p-6 bg-white/5 border border-white/10 rounded-2xl">
          <span className="text-xs text-white/40 uppercase tracking-widest font-mono">Max Engagement</span>
          <div className="text-3xl font-black mt-1 text-pink-400">
            {summary?.best_engagement_value ? `${Number(summary.best_engagement_value).toFixed(2)}%` : `${Math.max(...rankings.map(r=>r.engagement_rate||0)).toFixed(2)}%`}
          </div>
        </div>
        <div className="glass-card p-6 bg-white/5 border border-white/10 rounded-2xl">
          <span className="text-xs text-white/40 uppercase tracking-widest font-mono">Highest View Tracker</span>
          <div className="text-3xl font-black mt-1 text-blue-400">
            {summary?.most_views_value && summary.most_views_value > 0 ? summary.most_views_value.toLocaleString() : Math.max(...rankings.map(r=>r.views||0)).toLocaleString()}
          </div>
        </div>
        <div className="glass-card p-6 bg-white/5 border border-white/10 rounded-2xl">
          <span className="text-xs text-white/40 uppercase tracking-widest font-mono">Average Density</span>
          <div className="text-3xl font-black mt-1 text-amber-400">
            {(rankings.reduce((acc, r) => acc + (r.engagement_rate || 0), 0) / rankings.length).toFixed(2)}%
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="glass-card p-6 bg-white/5 border border-white/10 rounded-2xl">
          <h4 className="text-sm font-bold uppercase tracking-wider text-white/70 mb-4">Engagement Rate Audit (%)</h4>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={rankings}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="creator" tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }} />
              <YAxis tick={{ fill: 'rgba(255,255,255,0.5)' }} />
              <Tooltip contentStyle={{ backgroundColor: '#111', border: '1px solid rgba(255,255,255,0.1)' }} />
              <Bar dataKey="engagement_rate" fill="#f43f5e" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="glass-card p-6 bg-white/5 border border-white/10 rounded-2xl">
          <h4 className="text-sm font-bold uppercase tracking-wider text-white/70 mb-4">
            {hasFollowerData ? "Views Per Follower Multiplier" : "Absolute Verified Reach (Views)"}
          </h4>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={rankings}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="creator" tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }} />
              <YAxis tick={{ fill: 'rgba(255,255,255,0.5)' }} />
              <Tooltip contentStyle={{ backgroundColor: '#111', border: '1px solid rgba(255,255,255,0.1)' }} />
              <Bar dataKey={hasFollowerData ? "views_per_follower" : "views"} fill={themeColor} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}