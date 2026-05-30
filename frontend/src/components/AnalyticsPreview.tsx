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

  const chartData = rankings.slice(0, 5).map(v => ({
    name: v.title?.substring(0, 25) || v.video_id,
    engagement: v.engagement_rate
  }));

  const hookChartData = profiles.map(p => ({
    name: p.title?.substring(0, 25) || p.video_id,
    hookScore: p.hook_score
  }));

  return (
    <div className="mb-6 space-y-6">
      <h2 className="text-2xl font-bold">Analytics Snapshot</h2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-white p-3 rounded-lg shadow text-center">
          <div className="text-xs text-gray-500">Videos</div>
          <div className="text-xl font-bold">{summary.count}</div>
        </div>
        <div className="bg-white p-3 rounded-lg shadow text-center">
          <div className="text-xs text-gray-500">Best Engagement</div>
          <div className="text-xl font-bold">{summary.best_engagement_value}%</div>
          <div className="text-xs truncate">{summary.best_engagement}</div>
        </div>
        <div className="bg-white p-3 rounded-lg shadow text-center">
          <div className="text-xs text-gray-500">Most Views</div>
          <div className="text-xl font-bold">{summary.most_views_value?.toLocaleString()}</div>
          <div className="text-xs truncate">{summary.most_views_title}</div>
        </div>
        <div className="bg-white p-3 rounded-lg shadow text-center">
          <div className="text-xs text-gray-500">Avg Engagement</div>
          <div className="text-xl font-bold">{summary.average_engagement}%</div>
        </div>
      </div>

      {chartData.length > 1 && (
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-sm font-medium mb-2">Engagement Comparison</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" tick={{fontSize: 10}} angle={-20} textAnchor="end" height={60} />
              <YAxis unit="%" />
              <Tooltip />
              <Bar dataKey="engagement" fill="#8b5cf6" name="Engagement %" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {hookChartData.length > 0 && (
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-sm font-medium mb-2">🎣 Hook Scores (0-10)</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={hookChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" tick={{fontSize: 10}} angle={-20} textAnchor="end" height={60} />
              <YAxis domain={[0, 10]} />
              <Tooltip />
              <Bar dataKey="hookScore" fill="#f59e0b" name="Hook Score" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}