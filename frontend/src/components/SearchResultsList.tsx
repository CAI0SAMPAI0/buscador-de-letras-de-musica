"use client";

import React, { useState } from "react";
import { ResultCard, SearchResultItem } from "./ResultCard";
import { Music, Filter, Clock } from "lucide-react";

interface SearchResultsListProps {
  results: SearchResultItem[];
  durationMs: number;
  query: string;
  hasSearched: boolean;
}

export const SearchResultsList: React.FC<SearchResultsListProps> = ({
  results,
  durationMs,
  query,
  hasSearched,
}) => {
  const [filterSource, setFilterSource] = useState<"all" | "google_drive" | "local">("all");

  const filteredResults = results.filter((item) => {
    if (filterSource === "all") return true;
    return item.source === filterSource;
  });

  if (!hasSearched) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <div className="w-16 h-16 rounded-2xl bg-sacred-card border border-sacred-accent/30 mx-auto flex items-center justify-center text-sacred-secondary mb-4 shadow-inner">
          <Music className="w-8 h-8 opacity-75" />
        </div>
        <h2 className="text-xl font-bold text-sacred-primary mb-2">
          Encontre os Cantos da Missa Rapidamente
        </h2>
        <p className="text-sm text-sacred-subtext max-w-md mx-auto">
          Digite um trecho da música, refrão ou título da apresentação acima para buscar nos arquivos indexados.
        </p>
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12 text-center">
        <div className="bg-sacred-card/70 border border-sacred-accent/40 rounded-2xl p-8 max-w-md mx-auto">
          <p className="text-base font-semibold text-sacred-primary mb-1">
            Nenhum resultado encontrado para &ldquo;{query}&rdquo;
          </p>
          <p className="text-xs text-sacred-subtext">
            Verifique a ortografia ou certifique-se de que os arquivos correspondentes foram indexados na pasta do Google Drive ou PC.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Controls and filters bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6 pb-4 border-b border-sacred-accent/20">
        <div className="flex items-center gap-3">
          <span className="text-sm font-bold text-sacred-primary">
            {filteredResults.length} {filteredResults.length === 1 ? "resultado" : "resultados"}
          </span>
          <span className="text-xs text-sacred-subtext flex items-center gap-1 font-mono">
            <Clock className="w-3.5 h-3.5" />
            {durationMs.toFixed(1)} ms
          </span>
        </div>

        {/* Source filter buttons */}
        <div className="flex items-center gap-1.5 p-1 rounded-xl bg-sacred-surface border border-sacred-accent/30 self-start sm:self-auto">
          <button
            onClick={() => setFilterSource("all")}
            className={`text-xs font-semibold px-3 py-1 rounded-lg transition-all ${
              filterSource === "all"
                ? "bg-sacred-secondary text-sacred-tertiary shadow"
                : "text-sacred-subtext hover:text-sacred-primary"
            }`}
          >
            Todas ({results.length})
          </button>
          <button
            onClick={() => setFilterSource("google_drive")}
            className={`text-xs font-semibold px-3 py-1 rounded-lg transition-all ${
              filterSource === "google_drive"
                ? "bg-sacred-secondary text-sacred-tertiary shadow"
                : "text-sacred-subtext hover:text-sacred-primary"
            }`}
          >
            Google Drive ({results.filter((r) => r.source === "google_drive").length})
          </button>
          <button
            onClick={() => setFilterSource("local")}
            className={`text-xs font-semibold px-3 py-1 rounded-lg transition-all ${
              filterSource === "local"
                ? "bg-sacred-secondary text-sacred-tertiary shadow"
                : "text-sacred-subtext hover:text-sacred-primary"
            }`}
          >
            Local ({results.filter((r) => r.source === "local").length})
          </button>
        </div>
      </div>

      {/* Results grid: 1 coluna em sm, 2 colunas em md, 3 colunas em lg/xl */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {filteredResults.map((item, index) => (
          <ResultCard key={index} item={item} searchQuery={query} />
        ))}
      </div>
    </div>
  );
};
