"use client";

import React, { useState } from "react";
import { Cloud, Folder, ExternalLink, MapPin, Check, Copy } from "lucide-react";
import { API_BASE_URL } from "../lib/api";

export interface SearchResultItem {
  file_name: string;
  folder_name: string;
  source: string;
  location: string;
  page?: number | null;
  slide?: number | null;
  snippet: string;
  score: number;
  file_path: string;
  open_url?: string | null;
}

interface ResultCardProps {
  item: SearchResultItem;
  searchQuery: string;
}

export const ResultCard: React.FC<ResultCardProps> = ({ item, searchQuery }) => {
  const [copied, setCopied] = useState(false);

  const isDrive = item.source === "google_drive";

  const handleOpen = async () => {
    if (isDrive && item.open_url) {
      window.open(item.open_url, "_blank", "noopener,noreferrer");
    } else if (item.open_url && item.open_url.startsWith("http")) {
      window.open(item.open_url, "_blank", "noopener,noreferrer");
    } else {
      // Local file: abre a pasta no Explorer com o arquivo selecionado e copia caminho
      try {
        await fetch(`${API_BASE_URL}/api/v1/files/open-local`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ file_path: item.file_path }),
        });
      } catch {
        // Fallback silencioso
      }
      navigator.clipboard.writeText(item.file_path);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    }
  };

  // Helper function to highlight search words in snippet
  const renderHighlightedSnippet = (text: string, query: string) => {
    if (!query) return text;
    const words = query
      .split(/\s+/)
      .filter((w) => w.length > 1)
      .map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
    if (words.length === 0) return text;

    const regex = new RegExp(`(${words.join("|")})`, "gi");
    const parts = text.split(regex);

    return parts.map((part, i) =>
      regex.test(part) ? (
        <mark
          key={i}
          className="bg-sacred-secondary/35 text-sacred-secondary font-semibold rounded px-1 py-0.5"
        >
          {part}
        </mark>
      ) : (
        part
      )
    );
  };

  return (
    <div className="bg-sacred-card hover:bg-sacred-cardHover border border-sacred-accent/30 hover:border-sacred-accent/60 rounded-2xl p-5 transition-all shadow-md hover:shadow-xl group flex flex-col justify-between h-full">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3">
        <div className="flex items-center gap-2.5 flex-wrap">
          <span
            className={`inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full border ${
              isDrive
                ? "bg-emerald-950/60 text-emerald-300 border-emerald-600/40"
                : "bg-blue-950/60 text-blue-300 border-blue-600/40"
            }`}
          >
            {isDrive ? <Cloud className="w-3.5 h-3.5" /> : <Folder className="w-3.5 h-3.5" />}
            <span>{isDrive ? "Google Drive" : "Pasta Local"}</span>
          </span>

          <span className="inline-flex items-center gap-1 text-xs font-bold px-2.5 py-1 rounded-full bg-sacred-surface text-sacred-secondary border border-sacred-accent/40">
            <MapPin className="w-3 h-3 text-sacred-accent" />
            <span>{item.location}</span>
          </span>

          <span className="text-xs text-sacred-subtext font-medium">
            Pasta: <strong className="text-sacred-primary">{item.folder_name}</strong>
          </span>
        </div>

        <button
          onClick={handleOpen}
          className="self-start sm:self-auto shrink-0 inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg bg-sacred-surface hover:bg-sacred-accent/20 text-sacred-secondary border border-sacred-accent/40 hover:border-sacred-secondary transition-all shadow-sm active:scale-95"
          title={isDrive ? "Abrir arquivo no navegador" : "Copiar caminho local"}
        >
          {isDrive ? (
            <>
              <ExternalLink className="w-3.5 h-3.5" />
              <span>Abrir no Drive</span>
            </>
          ) : copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-emerald-300">Aberto / Copiado!</span>
            </>
          ) : (
            <>
              <Folder className="w-3.5 h-3.5" />
              <span>Abrir no PC</span>
            </>
          )}
        </button>
      </div>

      <h3 className="text-base sm:text-lg font-bold text-sacred-primary mb-2 group-hover:text-sacred-secondary transition-colors">
        {item.file_name}
      </h3>

      <div className="bg-sacred-surface/80 rounded-xl p-3.5 border border-sacred-accent/20 text-sm leading-relaxed text-sacred-subtext font-mono italic whitespace-pre-wrap flex-1">
        &ldquo;{renderHighlightedSnippet(item.snippet, searchQuery)}&rdquo;
      </div>
    </div>
  );
};
