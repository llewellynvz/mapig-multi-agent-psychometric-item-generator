"use client";

import * as React from "react";
import { ChevronDown, Copy, ExternalLink, FileText, Globe, Link2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/components/ui/use-toast";
import type { AuditMetadata } from "@/lib/types";
import { RunTimeline } from "./RunTimeline";

export interface EvidenceAuditPanelProps {
  audit: AuditMetadata;
}

function isHttpSource(source: string): boolean {
  return /^https?:\/\//i.test(source);
}

function getSourceLabel(source: string): string {
  if (!isHttpSource(source)) return source;

  try {
    const parsed = new URL(source);
    return `${parsed.hostname}${parsed.pathname}` || source;
  } catch {
    return source;
  }
}

function getDomain(source: string): string {
  try {
    return new URL(source).hostname;
  } catch {
    return "unknown";
  }
}

function copyToClipboard(text: string, label: string, toast: ReturnType<typeof useToast>["toast"]) {
  navigator.clipboard.writeText(text).then(
    () => toast({ title: "Copied", description: `${label} copied to clipboard.`, variant: "default" }),
    () => toast({ title: "Copy failed", description: "Could not copy to clipboard.", variant: "default" })
  );
}

interface SourceListProps {
  sources: string[];
}

function SourceList({ sources }: SourceListProps) {
  const { toast } = useToast();

  if (sources.length === 0) {
    return <p className="text-sm text-muted-foreground">No sources in this section.</p>;
  }

  return (
    <div className="space-y-2">
      {sources.map((source, index) => {
        const isLink = isHttpSource(source);
        return (
          <div
            key={`${source}-${index}`}
            className="flex items-start justify-between gap-3 rounded-2xl border border-white/15 bg-white/10 p-3"
          >
            <div className="min-w-0 space-y-1">
              <div className="flex items-center gap-2">
                {isLink ? (
                  <Link2 className="h-4 w-4 shrink-0 text-accent" />
                ) : (
                  <FileText className="h-4 w-4 shrink-0 text-slate-200" />
                )}
                <Badge variant={isLink ? "default" : "outline"} className="font-normal">
                  {isLink ? "Web source" : "Local source"}
                </Badge>
              </div>
              {isLink ? (
                <a
                  href={source}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 break-all text-sm text-accent-light hover:underline"
                >
                  {getSourceLabel(source)}
                  <ExternalLink className="h-3.5 w-3.5" />
                </a>
              ) : (
                <code className="block break-all rounded-lg bg-white/10 px-2 py-1 text-xs text-slate-100">{source}</code>
              )}
              {isLink && (
                <p className="break-all text-xs text-slate-200/85">{source}</p>
              )}
            </div>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={() => copyToClipboard(source, "Source", toast)}
              aria-label="Copy source"
              className="shrink-0"
            >
              <Copy className="h-4 w-4" />
            </Button>
          </div>
        );
      })}
    </div>
  );
}

interface SourceSectionProps {
  title: string;
  count: number;
  icon: React.ReactNode;
  defaultOpen?: boolean;
  children: React.ReactNode;
}

function SourceSection({ title, count, icon, defaultOpen = false, children }: SourceSectionProps) {
  const [isOpen, setIsOpen] = React.useState(defaultOpen);

  return (
    <section className="rounded-2xl border border-white/15 bg-white/5 p-3 transition-colors hover:bg-white/10">
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        className="flex w-full items-center justify-between gap-2 text-left"
      >
        <div className="flex items-center gap-2">
          {icon}
          <p className="text-sm font-semibold text-slate-50">{title}</p>
          <Badge variant="secondary">{count}</Badge>
        </div>
        <ChevronDown className={`h-4 w-4 transition-transform ${isOpen ? "rotate-180" : ""}`} />
      </button>
      {isOpen && <div className="mt-3">{children}</div>}
    </section>
  );
}

export function EvidenceAuditPanel({ audit }: EvidenceAuditPanelProps) {
  const [isOpen, setIsOpen] = React.useState(true);
  const webSources = audit.approved_sources.filter(isHttpSource);
  const localSources = audit.approved_sources.filter((source) => !isHttpSource(source));

  const groupedWebSources = webSources.reduce<Record<string, string[]>>((acc, source) => {
    const domain = getDomain(source);
    acc[domain] = [...(acc[domain] || []), source];
    return acc;
  }, {});
  const orderedDomains = Object.keys(groupedWebSources).sort((a, b) => a.localeCompare(b));

  return (
    <Card className="glass-panel shadow-sm">
      <CardHeader className="border-b border-border/60">
        <div className="flex items-center justify-between gap-3">
          <CardTitle className="text-base md:text-lg">Evidence and Audit Trail</CardTitle>
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={() => setIsOpen((prev) => !prev)}
            className="min-w-[120px] bg-primary text-white hover:bg-accent hover:text-white"
          >
            {isOpen ? "Hide details" : "Show details"}
            <ChevronDown className={`ml-2 h-4 w-4 transition-transform ${isOpen ? "rotate-180" : ""}`} />
          </Button>
        </div>
      </CardHeader>
      {isOpen && (
        <CardContent className="space-y-5 pt-5">
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold text-muted-foreground">Approved sources</p>
            <Badge variant="secondary">{audit.approved_sources.length}</Badge>
          </div>
          {audit.approved_sources.length === 0 ? (
            <p className="text-sm text-muted-foreground">No approved sources were attached to this run.</p>
          ) : (
            <div className="space-y-3">
              <SourceSection
                title="Web Sources by Domain"
                count={webSources.length}
                icon={<Globe className="h-4 w-4 text-accent" />}
                defaultOpen
              >
                {orderedDomains.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No web sources.</p>
                ) : (
                  <div className="space-y-3">
                    {orderedDomains.map((domain) => (
                      <SourceSection
                        key={domain}
                        title={domain}
                        count={groupedWebSources[domain].length}
                        icon={<Link2 className="h-4 w-4 text-accent" />}
                      >
                        <SourceList sources={groupedWebSources[domain]} />
                      </SourceSection>
                    ))}
                  </div>
                )}
              </SourceSection>

              <SourceSection
                title="Local Curated Sources"
                count={localSources.length}
                icon={<FileText className="h-4 w-4 text-slate-200" />}
              >
                <SourceList sources={localSources} />
              </SourceSection>
            </div>
          )}
        </section>

        <section className="grid gap-3 sm:grid-cols-2">
          <div className="space-y-2 rounded-2xl border border-white/15 bg-white/10 p-3">
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Thread ID</p>
            <code className="block break-all text-xs">{audit.thread_id}</code>
          </div>
          <div className="space-y-2 rounded-2xl border border-white/15 bg-white/10 p-3">
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Run ID</p>
            <code className="block break-all text-xs">{audit.run_id}</code>
          </div>
        </section>

        <section className="space-y-2 rounded-2xl border border-white/15 bg-white/10 p-3">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Run summary</p>
          <p className="text-sm">
            Iterations: <span className="font-semibold">{audit.iteration_count}</span>
          </p>
          <p className="text-sm">
            Stop reason: <span className="font-semibold">{audit.stop_reason || "Not provided"}</span>
          </p>
          <RunTimeline iterationCount={audit.iteration_count} />
        </section>

        <section className="rounded-2xl border border-accent/35 bg-accent/15 p-3">
          <p className="text-sm font-semibold">About this panel</p>
          <p className="mt-1 text-xs text-slate-100/90">
            Approved sources are the references the workflow relied on during the run. Expand the sections to inspect
            clickable web sources or internal local references.
          </p>
        </section>
        </CardContent>
      )}
    </Card>
  );
}
