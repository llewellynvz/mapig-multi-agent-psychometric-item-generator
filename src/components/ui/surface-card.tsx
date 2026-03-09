"use client";

import * as React from "react";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export interface SurfaceCardProps extends React.HTMLAttributes<HTMLDivElement> {}

export function SurfaceCard({ className, ...props }: SurfaceCardProps) {
  return <Card className={cn("surface-card", className)} {...props} />;
}

export interface InsetPanelProps extends React.HTMLAttributes<HTMLDivElement> {}

export function InsetPanel({ className, ...props }: InsetPanelProps) {
  return <div className={cn("inset-panel", className)} {...props} />;
}

