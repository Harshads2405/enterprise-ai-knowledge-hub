import type { Citation } from "@/lib/api/conversations";

type CitationListProps = {
  sources: Citation[];
};

export default function CitationList({
  sources,
}: CitationListProps) {
  if (sources.length === 0) {
    return null;
  }

  return (
    <div className="message-sources">
      <p className="sources-title">Sources</p>

      {sources.map((source, index) => (
        <div
          key={`${source.document_id}-${source.chunk_id ?? index}`}
          className="source-item"
        >
          <div className="source-item-header">
            <span className="source-item-title">
              {source.document_title ??
                source.source_name ??
                `Document ${source.document_id}`}
            </span>

            {source.page !== undefined &&
              source.page !== null && (
                <small>Page {source.page}</small>
              )}
          </div>

          {source.chunk_index !== undefined && (
            <span className="source-item-chunk">
              Chunk {source.chunk_index}
            </span>
          )}

          <div className="source-item-scores">
            {source.retrieval_score !== undefined && (
              <span className="source-item-score">
                Retrieval: {source.retrieval_score.toFixed(2)}
              </span>
            )}

            {source.reranker_score !== undefined &&
              source.reranker_score !== null && (
                <span className="source-item-score">
                  Reranker: {source.reranker_score.toFixed(2)}
                </span>
              )}
          </div>
        </div>
      ))}
    </div>
  );
}