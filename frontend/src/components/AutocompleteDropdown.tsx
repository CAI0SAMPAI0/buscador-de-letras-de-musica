"use client";

import React, { useEffect, useRef } from "react";
import { Music2, ArrowUpRight } from "lucide-react";

interface AutocompleteDropdownProps {
  suggestions: string[];
  selectedIndex: number;
  onSelect: (item: string) => void;
  query: string;
}

export const AutocompleteDropdown: React.FC<AutocompleteDropdownProps> = ({
  suggestions,
  selectedIndex,
  onSelect,
  query,
}) => {
  const itemRefs = useRef<(HTMLButtonElement | null)[]>([]);

  useEffect(() => {
    if (selectedIndex >= 0 && itemRefs.current[selectedIndex]) {
      itemRefs.current[selectedIndex]?.scrollIntoView({ block: "nearest", behavior: "smooth" });
    }
  }, [selectedIndex]);

  if (suggestions.length === 0) return null;

  return (
    <div className="absolute left-0 right-0 top-full mt-1.5 z-40 bg-sacred-surface border border-sacred-accent/60 rounded-xl shadow-2xl overflow-hidden">
      <div className="px-3 py-1.5 text-[11px] font-semibold tracking-wider text-sacred-subtext uppercase border-b border-sacred-accent/20 bg-sacred-tertiary/60 flex items-center justify-between">
        <span>Sugestões ({suggestions.length})</span>
        <span className="text-[10px] text-sacred-subtext/70">Role para ver mais • Use ↑ ↓ e Enter</span>
      </div>
      <div className="max-h-56 overflow-y-auto divide-y divide-sacred-accent/15 sacred-scrollbar">
        {suggestions.map((suggestion, index) => {
          const isSelected = index === selectedIndex;
          return (
            <button
              key={index}
              ref={(el) => { itemRefs.current[index] = el; }}
              type="button"
              onClick={() => onSelect(suggestion)}
              className={`w-full text-left px-4 py-3 flex items-center justify-between gap-3 text-sm transition-colors ${
                isSelected
                  ? "bg-sacred-card text-sacred-secondary"
                  : "text-sacred-primary hover:bg-sacred-card/70 hover:text-sacred-secondary"
              }`}
            >
              <div className="flex items-center gap-2.5 min-w-0">
                <Music2 className={`w-4 h-4 shrink-0 ${isSelected ? "text-sacred-secondary" : "text-sacred-accent"}`} />
                <span className="truncate font-medium">{suggestion}</span>
              </div>
              <ArrowUpRight className="w-3.5 h-3.5 opacity-50 shrink-0" />
            </button>
          );
        })}
      </div>
    </div>
  );
};
