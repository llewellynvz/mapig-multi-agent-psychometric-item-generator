"use client";

import { useTheme } from "next-themes";
import { Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useHealth } from "@/hooks/useHealth";
import { cn } from "@/lib/utils";

export function TopBar() {
  const { theme, setTheme } = useTheme();
  const { status } = useHealth();

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-14 items-center justify-between px-4 lg:px-6">
        <div className="flex items-center gap-2">
          <span className="text-lg font-semibold text-primary">MAPIG</span>
        </div>
        <div className="flex items-center gap-3">
          <Badge
            variant="outline"
            className="font-normal text-muted-foreground"
          >
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
