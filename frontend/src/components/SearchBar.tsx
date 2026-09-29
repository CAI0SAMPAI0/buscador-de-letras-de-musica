"use client";

import React, { useState, useEffect, useRef } from "react";
import { Search, X, Loader2 } from "lucide-react";
import { AutocompleteDropdown } from "./AutocompleteDropdown";
import { API_BASE_URL } from "../lib/api";

interface SearchBarProps {
  onSearch: (query: string) => void;
  isLoading: boolean;
}

export const SearchBar: React.FC<SearchBarProps> = ({ onSearch, isLoading }) => {
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [selectedIndex, setSelectedIndex] = useState<number>(-1);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [warningMessage, setWarningMessage] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Debounced autocomplete suggestions fetching
  useEffect(() => {
    const trimmed = query.trim();
    if (trimmed.length < 2) {
      setSuggestions([]);
      setIsDropdownOpen(false);
      return;
    }

    const timer = setTimeout(async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/v1/search/suggestions?q=${encodeURIComponent(trimmed)}`);
        if (res.ok) {
          const data: string[] = await res.json();
          setSuggestions(data.slice(0, 15));
          setIsDropdownOpen(data.length > 0);
          setSelectedIndex(-1);
        }
      } catch (err) {
        // Ignora silenciosamente se API estiver offline
      }
    }, 200);

    return () => clearTimeout(timer);
  }, [query]);

  // Handle outside clicks to close dropdown
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSubmit = (searchQuery: string = query) => {
    const trimmed = searchQuery.trim();
    const words = trimmed.split(/\s+/).filter(Boolean);

    if (words.length < 2) {
      setWarningMessage("⚠️ Por favor, digite pelo menos 2 palavras para maior precisão (ex: 'nós vos damos graças')");
      return;
    }

    setWarningMessage(null);
    setIsDropdownOpen(false);
    onSearch(trimmed);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!isDropdownOpen || suggestions.length === 0) {
      if (e.key === "Enter") {
        e.preventDefault();
        handleSubmit();
      }
      return;
    }

    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev < suggestions.length - 1 ? prev + 1 : 0));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev > 0 ? prev - 1 : suggestions.length - 1));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
        const selected = suggestions[selectedIndex];
        setQuery(selected);
        handleSubmit(selected);
      } else {
        handleSubmit();
      }
    } else if (e.key === "Escape") {
      setIsDropdownOpen(false);
    }
  };

  const handleSelectSuggestion = (item: string) => {
    setQuery(item);
    handleSubmit(item);
  };

  return (
    <div className="w-full max-w-4xl mx-auto px-4" ref={containerRef}>
      <div className="relative">
        <div className="relative flex items-center bg-sacred-surface border-2 border-sacred-accent/50 focus-within:border-sacred-secondary rounded-2xl shadow-xl shadow-sacred-tertiary/50 transition-all p-1.5">
          <div className="pl-3.5 pr-2 text-sacred-accent">
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin text-sacred-secondary" />
            ) : (
              <Search className="w-5 h-5" />
            )}
          </div>

          <input
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setWarningMessage(null);
            }}
            onKeyDown={handleKeyDown}
            onFocus={() => {
              if (suggestions.length > 0) setIsDropdownOpen(true);
            }}
            placeholder="Digite o título, refrão ou trecho da música (mínimo 2 palavras)..."
            className="w-full bg-transparent text-sacred-primary placeholder-sacred-subtext/60 text-base sm:text-lg outline-none px-2 py-2"
          />

          {query && (
            <button
              type="button"
              onClick={() => {
                setQuery("");
                setSuggestions([]);
                setIsDropdownOpen(false);
                setWarningMessage(null);
              }}
              className="p-1.5 rounded-full hover:bg-sacred-card text-sacred-subtext hover:text-sacred-primary transition-colors mr-1"
            >
              <X className="w-4 h-4" />
            </button>
          )}

          <button
            type="button"
            onClick={() => handleSubmit()}
            disabled={isLoading}
            className="shrink-0 px-5 sm:px-7 py-2.5 rounded-xl font-bold text-sm sm:text-base bg-gradient-to-r from-sacred-secondary to-sacred-accent hover:from-sacred-secondary/90 hover:to-sacred-accent/90 text-sacred-tertiary shadow-md hover:shadow-lg transition-all active:scale-[0.98] disabled:opacity-50"
          >
            Pesquisar
          </button>
        </div>

        {isDropdownOpen && (
          <AutocompleteDropdown
            suggestions={suggestions}
            selectedIndex={selectedIndex}
            onSelect={handleSelectSuggestion}
            query={query}
          />
        )}
      </div>

      {warningMessage && (
        <div className="mt-2 text-xs sm:text-sm text-amber-300 font-medium px-2 py-1 flex items-center gap-1.5 animate-fadeIn">
          {warningMessage}
        </div>
      )}
    </div>
  );
};
