interface Props {
  sources: { video_id: string; chunk_id: number | null }[];
}

export default function SourceCitation({ sources }: Props) {
  if (!sources.length) return null;

  return (
    <div className="mt-2 text-xs text-gray-500">
      <span className="font-medium">Sources: </span>
      {sources.map((s, i) => (
        <span key={i} className="mr-2">
          {s.chunk_id
            ? `Video ${s.video_id} Chunk ${s.chunk_id}`
            : `Video ${s.video_id} metadata`}
          {i < sources.length - 1 ? ', ' : ''}
        </span>
      ))}
    </div>
  );
}