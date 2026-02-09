"use client";

import * as React from "react";
import { Copy } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
  TooltipProvider,
} from "@/components/ui/tooltip";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/use-toast";
import type { AuditMetadata } from "@/lib/types";
import { RunTimeline } from "./RunTimeline";

export interface EvidenceAuditPanelProps {
  audit: AuditMetadata;
}

function copyToClipboard(text: string, label: string, toast: ReturnType<typeof useToast>["toast"]) {
  navigator.clipboard.writeText(text).then(
    () => toast({ title: "Copied", description: `${label} copied to clipboard.`, variant: "default" }),
    () => toast({ title: "Copy failed", description: "Could not copy to clipboard.", variant: "destructive" })
  );
}

export function EvidenceAuditPanel({ audit }: EvidenceAuditPanelProps) {
  const { toast } = useToast();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Evidence and Audit</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <p className="text-sm font-medium text-muted-foreground">Approved sources</p>
          <div className="flex flex-wrap gap-2">
            {audit.approved_sources.length === 0 ? (
              <span className="text-sm text-muted-foreground">None</span>
            ) : (
              audit.approved_sources.map((src, i) => (
                <TooltipProvider key={`${src}-${i}`}>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Badge variant="secondary" className="max-w-[200px] truncate font-normal">
                        {src}
                      </Badge>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p className="max-w-xs break-all">{src}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              ))
            )}
          </div>
        </div>

        <div className="space-y-2">
          <p className="text-sm font-medium text-muted-foreground">Thread ID</p>
          <div className="flex items-center gap-2">
            <code className="flex-1 truncate rounded-lg bg-muted px-2 py-1 text-xs">
              {audit.thread_id}
            </code>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => copyToClipboard(audit.thread_id, "Thread ID", toast)}
              aria-label="Copy thread ID"
            >
              <Copy className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <div className="space-y-2">
          <p className="text-sm font-medium text-muted-foreground">Run ID</p>
          <div className="flex items-center gap-2">
            <code className="flex-1 truncate rounded-lg bg-muted px-2 py-1 text-xs">
              {audit.run_id}
            </code>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => copyToClipboard(audit.run_id, "Run ID", toast)}
              aria-label="Copy run ID"
            >
              <Copy className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <div className="space-y-2">
          <p className="text-sm font-medium text-muted-foreground">Run summary</p>
          <p className="text-sm">
            <span className="font-medium">Iterations:</span> {audit.iteration_count}
          </p>
          <p className="text-sm">
            <span className="font-medium">Stop reason:</span> {audit.stop_reason || "—"}
          </p>
        </div>

        <RunTimeline iterationCount={audit.iteration_count} />
      </CardContent>
    </Card>
  );
}
