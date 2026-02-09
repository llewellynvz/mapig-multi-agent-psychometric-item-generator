"use client";

import * as React from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { Button } from "@/components/ui/button";

export interface DeveloperDrawerProps {
  requestJson: string | null;
  responseJson: string | null;
}

export function DeveloperDrawer({ requestJson, responseJson }: DeveloperDrawerProps) {
  const [open, setOpen] = React.useState(false);

  const hasContent = requestJson !== null || responseJson !== null;

  return (
    <div className="border-t bg-muted/30">
      <Button
        variant="ghost"
        className="w-full justify-between rounded-none"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-controls="developer-drawer-content"
      >
        <span>Developer</span>
        {open ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
      </Button>
      {open && (
        <div
          id="developer-drawer-content"
          className="border-t px-4 py-4 space-y-4 max-h-[400px] overflow-auto"
        >
          {requestJson !== null && (
            <div>
              <p className="text-sm font-medium text-muted-foreground mb-2">Last request</p>
              <pre className="rounded-2xl bg-muted p-4 text-xs overflow-x-auto whitespace-pre-wrap break-words">
                {requestJson}
              </pre>
            </div>
          )}
          {responseJson !== null && (
            <div>
              <p className="text-sm font-medium text-muted-foreground mb-2">Last response</p>
              <pre className="rounded-2xl bg-muted p-4 text-xs overflow-x-auto whitespace-pre-wrap break-words">
                {responseJson}
              </pre>
            </div>
          )}
          {!hasContent && (
            <p className="text-sm text-muted-foreground">No request/response yet.</p>
          )}
        </div>
      )}
    </div>
  );
}
