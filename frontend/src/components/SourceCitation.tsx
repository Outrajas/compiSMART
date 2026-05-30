interface Props {
  sources: string[];   // now strings, not objects
}

export default function SourceCitation({ sources }: Props) {
  if (!sources.length) return null;

  return (
    <div className="mt-2 text-xs text-gray-500">
      <span className="font-medium">Sources: </span>
      {sources.map((s, i) => (
        <span key={i} className="mr-2">
          {s}
          {i < sources.length - 1 ? ' • ' : ''}
        </span>
      ))}
    </div>
  );
}