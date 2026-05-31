// frontend/src/components/StatsCard.tsx
interface Props {
  label: string;
  value: string | number;
}

export default function StatsCard({ label, value }: Props) {
  return (
    <div className="bg-white rounded-xl shadow-md p-5 text-center transition-all duration-300 hover:shadow-xl hover:-translate-y-1 border border-gray-100">
      <div className="text-sm text-gray-500 uppercase tracking-wide">{label}</div>
      <div className="text-3xl font-bold bg-gradient-to-r from-gray-800 to-gray-600 bg-clip-text text-transparent mt-1">
        {value}
      </div>
    </div>
  );
}