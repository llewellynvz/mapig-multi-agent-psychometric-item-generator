"use client";

import { useTheme } from "next-themes";
import { Activity, Moon, Sparkles, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useHealth } from "@/hooks/useHealth";
import { cn } from "@/lib/utils";

export function TopBar() {
  const { theme, setTheme } = useTheme();
  const { status } = useHealth();

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/70 bg-background/85 shadow-sm backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-16 items-center justify-between px-4 lg:px-6">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-primary/15 p-2">
            <Sparkles className="h-4 w-4 text-primary" />
          </div>
          <div>
            <p className="text-base font-semibold tracking-tight text-primary md:text-lg">MAPIG</p>
            <p className="hidden text-[0.72rem] text-muted-foreground md:block">
              Evidence-bounded, multi-agent item drafting for scale development
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Badge
            variant="outline"
            className="hidden items-center gap-1 font-normal text-muted-foreground sm:inline-flex"
          >
            <Activity className="h-3.5 w-3.5" />
            Local API
          </Badge>
          <span
            className={cn(
              "flex h-2 w-2 rounded-full",
              status === "ok" && "bg-accent",
              status === "error" && "bg-destructive",
              status === "pending" && "animate-pulse bg-muted"
            )}
            title={
              status === "ok"
                ? "Connected"
                : status === "error"
                  ? "Disconnected"
                  : "Checking..."
            }
            aria-label={
              status === "ok"
                ? "API connected"
                : status === "error"
                  ? "API disconnected"
                  : "Checking connection"
            }
          />
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          >
            <Sun className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
            <Moon className="absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
          </Button>
        </div>
      </div>
    </header>
  );
}
