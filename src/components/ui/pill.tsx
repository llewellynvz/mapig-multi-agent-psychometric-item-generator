"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

export interface PillProps extends React.HTMLAttributes<HTMLSpanElement> {}

export function Pill({ className, ...props }: PillProps) {
  return <span className={cn("ui-pill", className)} {...props} />;
}

