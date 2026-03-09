"use client";

import * as React from "react";
import { Button, type ButtonProps } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export interface PrimaryButtonProps extends ButtonProps {}

export function PrimaryButton({ className, ...props }: PrimaryButtonProps) {
  return <Button className={cn("btn-primary-ui", className)} {...props} />;
}

export interface SecondaryButtonProps extends ButtonProps {}

export function SecondaryButton({ className, ...props }: SecondaryButtonProps) {
  return <Button className={cn("btn-secondary-ui", className)} {...props} />;
}

