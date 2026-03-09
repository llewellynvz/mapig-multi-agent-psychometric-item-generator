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
    <div className="rounded-2xl border border-white/15 bg-[#0B2A34]/70">
      <Button
        variant="ghost"
        className="w-full justify-between rounded-none text-white hover:bg-accent hover:text-white"
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
          className="max-h-[400px] space-y-4 overflow-auto border-t border-white/15 px-4 py-4"
        >
          {requestJson !== null && (
            <div>
              <p className="mb-2 text-sm font-medium text-slate-200">Last request</p>
              <pre className="overflow-x-auto break-words whitespace-pre-wrap rounded-2xl bg-white/10 p-4 text-xs text-slate-100">
                {requestJson}
              </pre>
            </div>
          )}
          {responseJson !== null && (
            <div>
              <p className="mb-2 text-sm font-medium text-slate-200">Last response</p>
              <pre className="overflow-x-auto break-words whitespace-pre-wrap rounded-2xl bg-white/10 p-4 text-xs text-slate-100">
                {responseJson}
              </pre>
            </div>
          )}
          {!hasContent && (
            <p className="text-sm text-slate-200">No request/response yet.</p>
          )}
        </div>
      )}
    </div>
  );
}
