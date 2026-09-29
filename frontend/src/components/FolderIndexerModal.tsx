"use client";

import React, { useState } from "react";
import { X, Cloud, Folder, Zap, Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { API_BASE_URL } from "../lib/api";

interface FolderIndexerModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const FolderIndexerModal: React.FC<FolderIndexerModalProps> = ({
  isOpen,
  onClose,
}) => {
  const [localFolder, setLocalFolder] = useState("");
  const [driveUrl, setDriveUrl] = useState("https://drive.google.com/drive/folders/1GjTZ4umBib-7_PznEBx_w4EnNPZIafwU?usp=sharing");
  const [isIndexing, setIsIndexing] = useState(false);
  const [progressData, setProgressData] = useState<{
    status_message: string;
    progress_pct: number;
    files_processed: number;
    total_files: number;
    completed: boolean;
    error: string | null;
  } | null>(null);
  const [resultMessage, setResultMessage] = useState<{ text: string; success: boolean } | null>(null);

  if (!isOpen) return null;

  const handleIndex = async () => {
    if (!localFolder.trim() && !driveUrl.trim()) {
      setResultMessage({
        text: "Por favor, informe uma pasta local ou link do Google Drive para indexar.",
        success: false,
      });
      return;
    }

    setIsIndexing(true);
    setResultMessage(null);
    setProgressData({
      status_message: "Iniciando processo de indexação...",
      progress_pct: 5,
      files_processed: 0,
      total_files: 0,
      completed: false,
      error: null,
    });

    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/index/scan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          folder_path: localFolder.trim() || null,
          include_drive: Boolean(driveUrl.trim()),
          drive_url: driveUrl.trim() || null,
        }),
      });

      if (!res.ok) {
        const err = await res.text();
        setResultMessage({ text: `Falha ao iniciar indexação: ${err}`, success: false });
        setIsIndexing(false);
        return;
      }

      // Polling para acompanhar progresso real a cada 1 segundo
      const pollInterval = setInterval(async () => {
        try {
          const progRes = await fetch(`${API_BASE_URL}/api/v1/index/progress`);
          if (progRes.ok) {
            const data = await progRes.json();
            setProgressData(data);

            if (data.completed) {
              clearInterval(pollInterval);
              setIsIndexing(false);
              setResultMessage({
                text: `✅ ${data.status_message}`,
                success: true,
              });
            } else if (data.error) {
              clearInterval(pollInterval);
              setIsIndexing(false);
              setResultMessage({
                text: `❌ ${data.status_message}`,
                success: false,
              });
            }
          }
        } catch {
          // Continua polling em caso de oscilação momentânea
        }
      }, 1000);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setResultMessage({ text: `Erro de conexão com o servidor: ${msg}`, success: false });
      setIsIndexing(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 animate-fadeIn">
      <div className="bg-sacred-surface border border-sacred-accent/60 rounded-3xl p-6 sm:p-8 max-w-lg w-full shadow-2xl relative">
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-1.5 rounded-full hover:bg-sacred-card text-sacred-subtext hover:text-sacred-primary transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-sacred-card border border-sacred-accent/40 flex items-center justify-center text-sacred-secondary">
            <Zap className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg sm:text-xl font-bold text-sacred-primary">
              Indexar Músicas e Apresentações
            </h2>
            <p className="text-xs text-sacred-subtext">
              Sincronize novas pastas ou links para atualizar as músicas no buscador
            </p>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-sacred-subtext mb-1.5 flex items-center gap-1.5">
              <Folder className="w-3.5 h-3.5 text-sacred-accent" />
              <span>Pasta Local no Computador ou Pendrive</span>
            </label>
            <input
              type="text"
              value={localFolder}
              onChange={(e) => setLocalFolder(e.target.value)}
              placeholder="ex: C:\MinhasMusicas ou E:\Pendrive"
              className="w-full bg-sacred-tertiary border border-sacred-accent/40 focus:border-sacred-secondary rounded-xl px-3.5 py-2.5 text-sm text-sacred-primary placeholder-sacred-subtext/40 outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-sacred-subtext mb-1.5 flex items-center gap-1.5">
              <Cloud className="w-3.5 h-3.5 text-sacred-accent" />
              <span>Link de Pasta Compartilhada do Google Drive</span>
            </label>
            <input
              type="text"
              value={driveUrl}
              onChange={(e) => setDriveUrl(e.target.value)}
              placeholder="https://drive.google.com/drive/folders/..."
              className="w-full bg-sacred-tertiary border border-sacred-accent/40 focus:border-sacred-secondary rounded-xl px-3.5 py-2.5 text-sm text-sacred-primary placeholder-sacred-subtext/40 outline-none"
            />
          </div>

          {isIndexing && progressData && (
            <div className="bg-sacred-tertiary border border-sacred-accent/40 rounded-xl p-3.5 space-y-2 animate-fadeIn">
              <div className="flex justify-between items-center text-xs font-semibold text-sacred-secondary">
                <span className="truncate pr-2">{progressData.status_message}</span>
                <span className="shrink-0">{progressData.progress_pct}%</span>
              </div>
              <div className="w-full bg-sacred-card rounded-full h-2 overflow-hidden border border-sacred-accent/30">
                <div
                  className="bg-gradient-to-r from-sacred-accent to-sacred-secondary h-full rounded-full transition-all duration-300"
                  style={{ width: `${Math.max(5, progressData.progress_pct)}%` }}
                />
              </div>
              {progressData.total_files > 0 && (
                <p className="text-[11px] text-sacred-subtext text-right">
                  {progressData.files_processed} de {progressData.total_files} arquivos processados
                </p>
              )}
            </div>
          )}

          {resultMessage && (
            <div
              className={`p-3 rounded-xl text-xs font-medium flex items-center gap-2 ${
                resultMessage.success
                  ? "bg-emerald-950/60 text-emerald-300 border border-emerald-600/40"
                  : "bg-red-950/60 text-red-300 border border-red-600/40"
              }`}
            >
              {resultMessage.success ? (
                <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
              ) : (
                <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
              )}
              <span>{resultMessage.text}</span>
            </div>
          )}

          <div className="pt-2 flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-semibold text-sacred-subtext hover:text-sacred-primary transition-colors"
            >
              Fechar
            </button>
            <button
              type="button"
              onClick={handleIndex}
              disabled={isIndexing}
              className="px-6 py-2.5 rounded-xl font-bold text-xs sm:text-sm bg-gradient-to-r from-sacred-secondary to-sacred-accent text-sacred-tertiary shadow-md hover:shadow-lg transition-all flex items-center gap-2 disabled:opacity-50"
            >
              {isIndexing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Indexando...</span>
                </>
              ) : (
                <>
                  <Zap className="w-4 h-4" />
                  <span>Iniciar Indexação</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
