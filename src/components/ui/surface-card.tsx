"use client";

import * as React from "react";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export type SurfaceCardProps = React.HTMLAttributes<HTMLDivElement>;

export function SurfaceCard({ className, ...props }: SurfaceCardProps) {
  return <Card className={cn("surface-card", className)} {...props} />;
}

export type InsetPanelProps = React.HTMLAttributes<HTMLDivElement>;

export function InsetPanel({ className, ...props }: InsetPanelProps) {
  return <div className={cn("inset-panel", className)} {...props} />;
}

