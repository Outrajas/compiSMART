interface Props {
  label: string;
  value: string | number;
}

export default function StatsCard({ label, value }: Props) {
  return (
    <div className="bg-white p-4 rounded-xl shadow border text-center">
      <div className="text-sm text-gray-500">{label}</div>
      <div className="text-2xl font-bold">{value}</div>
    </div>
  );
}