"use client";

import * as React from "react";
import { Card } from "@/components/ui/card";
import { ChevronDown, ChevronUp } from "lucide-react";
import { Button } from "@/components/ui/button";

export function AppDescription() {
  const [isExpanded, setIsExpanded] = React.useState(false);

  return (
    <Card className="mb-6">
      <div className="p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <h1 className="text-2xl font-bold mb-2">
              MAPIG – Multi-Agent Psychometric Item Generator
            </h1>
            <p className="text-muted-foreground mb-4">
              Evidence-bounded, multi-agent item drafting for psychometric scale development
            </p>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsExpanded(!isExpanded)}
            aria-label={isExpanded ? "Collapse description" : "Expand description"}
          >
            {isExpanded ? (
              <ChevronUp className="h-5 w-5" />
            ) : (
              <ChevronDown className="h-5 w-5" />
            )}
          </Button>
        </div>

        {isExpanded && (
          <div className="mt-4 space-y-4 text-sm">
            <div>
              <h2 className="font-semibold mb-2">What this is</h2>
              <p className="text-muted-foreground mb-2">
                Psychometric item writing is sensitive to wording, context assumptions, and construct drift. MAPIG operationalises a conservative workflow:
              </p>
              <ul className="list-disc list-inside space-y-1 text-muted-foreground ml-4">
                <li>Strict JSON schemas between agents to reduce format drift and improve traceability</li>
                <li>Evidence-bounded retrieval with an approved-source policy</li>
                <li>Iterative review loops with explicit roles</li>
                <li>Audit metadata in every response for reproducibility</li>
              </ul>
              <p className="text-muted-foreground mt-3 italic">
                MAPIG produces item drafts and review artefacts. It does not replace human judgment, piloting, or validation.
              </p>
            </div>

            <div>
              <h2 className="font-semibold mb-2">How it works</h2>
              <p className="text-muted-foreground mb-2">
                MAPIG uses specialized agents that work together to generate and refine psychometric items:
              </p>
              <ul className="list-disc list-inside space-y-1 text-muted-foreground ml-4">
                <li>
                  <strong>WebSurfer Agent</strong>: retrieves construct-relevant academic evidence using Perplexity, constrained by an allowlist of approved domains
                </li>
                <li>
                  <strong>Local retrieval</strong>: pulls curated evidence from approved sources
                </li>
                <li>
                  <strong>Item Writer Agent</strong>: drafts items with rationales and evidence citations
                </li>
                <li>
                  <strong>Content Reviewer</strong>: checks construct fidelity and contamination with neighbor constructs
                </li>
                <li>
                  <strong>Linguistic Reviewer</strong>: checks clarity, ambiguity, readability, and wording hazards
                </li>
                <li>
                  <strong>Bias Reviewer</strong>: flags bias risk and likely DIF drivers
                </li>
                <li>
                  <strong>Meta Editor</strong>: revises items using reviewer comments while preserving construct coverage
                </li>
                <li>
                  <strong>Critic Agent</strong>: decides whether to iterate again or finalise, with explicit stop conditions
                </li>
              </ul>
            </div>

            <div>
              <h2 className="font-semibold mb-2">Approved sources policy</h2>
              <p className="text-muted-foreground">
                MAPIG supports two evidence channels: (1) Local approved sources from markdown files, and (2) Web retrieval restricted to allowlisted domains. Perplexity retrieval is blocked unless an allowlist is provided via environment variables or the API request.
              </p>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}
