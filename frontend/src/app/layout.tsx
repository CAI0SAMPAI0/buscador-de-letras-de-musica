import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Buscador de Músicas da Missa",
  description: "Localize músicas rapidamente em apresentações (PPT/PPTX), documentos (DOC/DOCX) e PDFs do PC ou Google Drive",
  icons: {
    icon: "/images/logo_catolicismo.webp",
    shortcut: "/images/logo_catolicismo.webp",
    apple: "/images/logo_catolicismo.webp",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <body className="bg-sacred-tertiary text-sacred-primary antialiased selection:bg-sacred-secondary selection:text-sacred-tertiary">
        {children}
      </body>
    </html>
  );
}
