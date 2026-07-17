"use client";

import * as React from "react";
import { CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SurfaceCard } from "@/components/ui/surface-card";

interface EmptyPanelProps {
  title: string;
  children: React.ReactNode;
  className?: string;
}

export function EmptyPanel({ title, children, className }: EmptyPanelProps) {
  return (
    <SurfaceCard className={className}>
      <CardHeader className="border-b border-border/60">
        <CardTitle className="text-base md:text-lg">{title}</CardTitle>
      </CardHeader>
      <CardContent className="pt-5">
        <p className="text-sm text-muted-foreground">{children}</p>
      </CardContent>
    </SurfaceCard>
  );
}
