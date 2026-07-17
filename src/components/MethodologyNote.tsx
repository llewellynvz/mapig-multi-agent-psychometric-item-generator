"use client";

import * as React from "react";

export interface MethodologyNoteProps {
  children?: React.ReactNode;
  embeddingModel?: string | null;
}

export function MethodologyNote({ children, embeddingModel }: MethodologyNoteProps) {
  return (
    <div className="mt-4 pt-4 border-t border-border/30">
      <p className="text-[11px] italic text-muted-foreground/70">{children}</p>
      {embeddingModel && (
        <p className="mt-1 text-[11px] italic text-muted-foreground/70">
          Embedding model: {embeddingModel}
        </p>
      )}
    </div>
  );
}
