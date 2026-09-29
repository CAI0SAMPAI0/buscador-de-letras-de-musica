"use client";

import React, { useState, useEffect } from "react";
import { Header } from "../components/Header";
import { SearchBar } from "../components/SearchBar";
import { SearchResultsList } from "../components/SearchResultsList";
import { FolderIndexerModal } from "../components/FolderIndexerModal";
import { SearchResultItem } from "../components/ResultCard";
import { ArrowUp } from "lucide-react";

import { API_BASE_URL } from "../lib/api";

export default function Home() {
  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [durationMs, setDurationMs] = useState(0);
  const [currentQuery, setCurrentQuery] = useState("");
  const [isIndexerOpen, setIsIndexerOpen] = useState(false);
  const [showScrollTop, setShowScrollTop] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setShowScrollTop(window.scrollY > 280);
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleSearch = async (query: string) => {
    setIsLoading(true);
    setCurrentQuery(query);
    setHasSearched(true);

    const startTime = performance.now();

    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });

      if (res.ok) {
        const data = await res.json();
        setResults(data.results || []);
        setDurationMs(data.duration_ms || (performance.now() - startTime));
      } else {
        setResults([]);
        setDurationMs(performance.now() - startTime);
      }
    } catch (err) {
      console.error("Erro ao realizar busca:", err);
      setResults([]);
      setDurationMs(performance.now() - startTime);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-sacred-tertiary">
      <Header onOpenIndexer={() => setIsIndexerOpen(true)} />

      <main className="flex-1 py-8 sm:py-12">
        <div className="max-w-4xl mx-auto px-4 mb-8 text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sacred-card border border-sacred-accent/30 text-xs font-semibold text-sacred-secondary mb-4 shadow-sm">
            <span>Busca Otimizada</span>
          </div>
          <h2 className="text-2xl sm:text-4xl font-extrabold text-sacred-primary tracking-tight mb-3">
            Localize Letras e Músicas da Liturgia
          </h2>
          <p className="text-sm sm:text-base text-sacred-subtext max-w-xl mx-auto">
            Digite pelo menos 2 palavras de um refrão, estrofe ou título para encontrar a página ou slide exato.
          </p>
        </div>

        <SearchBar onSearch={handleSearch} isLoading={isLoading} />

        <SearchResultsList
          results={results}
          durationMs={durationMs}
          query={currentQuery}
          hasSearched={hasSearched}
        />
      </main>

      <footer className="border-t border-sacred-accent/20 py-6 text-center text-xs text-sacred-subtext/70 bg-sacred-surface/40">
        <p>Buscador de Músicas da Missa &bull; Sistema Integrado com Google Drive e Pastas Locais</p>
      </footer>

      <FolderIndexerModal
        isOpen={isIndexerOpen}
        onClose={() => setIsIndexerOpen(false)}
      />

      {showScrollTop && (
        <button
          onClick={scrollToTop}
          className="fixed bottom-6 right-6 z-40 p-3.5 rounded-full bg-gradient-to-r from-sacred-secondary to-sacred-accent text-sacred-tertiary shadow-xl hover:shadow-2xl hover:scale-110 active:scale-95 transition-all duration-300 border border-sacred-primary/40 flex items-center justify-center group animate-fadeIn"
          title="Voltar ao início"
          aria-label="Voltar ao início da página"
        >
          <ArrowUp className="w-5 h-5 stroke-[2.5] group-hover:-translate-y-0.5 transition-transform" />
        </button>
      )}
    </div>
  );
}
