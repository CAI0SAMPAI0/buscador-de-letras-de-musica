"use client";

import React, { useEffect, useState } from "react";
import { Music, Cloud, Server, Sparkles, FolderSync } from "lucide-react";
import { API_BASE_URL } from "../lib/api";

interface HeaderProps {
  onOpenIndexer: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onOpenIndexer }) => {
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);

  useEffect(() => {
    const checkApi = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/v1/health`, { cache: "no-store" });
        setApiOnline(res.ok);
      } catch {
        setApiOnline(false);
      }
    };
    checkApi();
    const interval = setInterval(checkApi, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="border-b border-sacred-accent/30 bg-sacred-surface sticky top-0 z-30 px-4 sm:px-8 py-4 transition-all">
      <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-xl bg-sacred-card border border-sacred-accent/40 overflow-hidden flex items-center justify-center shadow-lg shadow-sacred-accent/20 shrink-0">
            <img src="/images/logo_catolicismo.webp" alt="Catolicismo" className="w-full h-full object-cover" />
          </div>
          <div>
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-sacred-primary flex items-center gap-2">
              Buscador de Músicas
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-sacred-accent/20 text-sacred-secondary border border-sacred-accent/40">
                Missa
              </span>
            </h1>
            <p className="text-xs text-sacred-subtext hidden sm:block">
              Pesquise letras e apresentações em PPT, PPTX, DOC, DOCX e PDF
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={onOpenIndexer}
            className="flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg bg-sacred-card hover:bg-sacred-cardHover text-sacred-primary border border-sacred-accent/40 transition-colors shadow-sm"
          >
            <FolderSync className="w-3.5 h-3.5 text-sacred-secondary" />
            <span>Indexar Pastas</span>
          </button>

          <div
            className={`flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg border transition-colors ${
              apiOnline === true
                ? "bg-emerald-950/40 text-emerald-300 border-emerald-700/50"
                : apiOnline === false
                ? "bg-amber-950/40 text-amber-300 border-amber-700/50"
                : "bg-sacred-card text-sacred-subtext border-sacred-accent/30"
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                apiOnline === true
                  ? "bg-emerald-400 animate-pulse"
                  : apiOnline === false
                  ? "bg-amber-400"
                  : "bg-zinc-400"
              }`}
            />
            <span>{apiOnline ? "API Online (8000)" : "API Offline"}</span>
          </div>
        </div>
      </div>
    </header>
  );
};
