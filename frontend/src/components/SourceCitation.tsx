// frontend/src/components/SourceCitation.tsx
interface Props {
  sources: string[];
}

export default function SourceCitation({ sources }: Props) {
  if (!sources.length) return null;

  return (
    <div className="mt-3 flex flex-wrap gap-2 text-xs">
      <span className="font-medium text-gray-500">Sources:</span>
      {sources.map((s, i) => (
        <span
          key={i}
          className="px-2 py-1 bg-gray-100 rounded-full text-gray-600 hover:bg-gray-200 transition-colors"
        >
          {s}
        </span>
      ))}
    </div>
  );
}