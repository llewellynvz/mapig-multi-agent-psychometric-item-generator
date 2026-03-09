"use client";

import * as React from "react";
import { MessageSquareText, RotateCw } from "lucide-react";
import { CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PrimaryButton } from "@/components/ui/action-buttons";
import { Label } from "@/components/ui/label";
import { InsetPanel, SurfaceCard } from "@/components/ui/surface-card";
import { Textarea } from "@/components/ui/textarea";

export interface HumanFeedbackPanelProps {
  value: string;
  isPending?: boolean;
  onChange: (value: string) => void;
  onRefine: () => void;
}

export function HumanFeedbackPanel({
  value,
  isPending = false,
  onChange,
  onRefine,
}: HumanFeedbackPanelProps) {
  return (
    <SurfaceCard className="border-lime-300/70">
      <CardHeader className="border-b border-border/60">
        <CardTitle className="flex items-center gap-2 text-base md:text-lg">
          <MessageSquareText className="h-5 w-5 text-white" />
          Human Feedback Loop
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-5">
        <InsetPanel className="space-y-4 rounded-2xl p-4">
          <p className="text-sm text-muted-foreground">
            Add reviewer guidance and run a refinement pass. The next run uses this feedback plus the current item set as
            context.
          </p>
          <div className="space-y-2">
            <Label htmlFor="human_feedback">Feedback for rerun</Label>
            <Textarea
              id="human_feedback"
              rows={5}
              value={value}
              placeholder="Example: Make items shorter, reduce overlap between Items 3 and 5, and increase emphasis on social inclusion."
              onChange={(e) => onChange(e.target.value)}
            />
          </div>
          <PrimaryButton
            type="button"
            onClick={onRefine}
            disabled={isPending || value.trim().length < 8}
            className="w-full sm:w-auto"
          >
            <RotateCw className="mr-2 h-4 w-4" />
            {isPending ? "Refining..." : "Refine with feedback"}
          </PrimaryButton>
        </InsetPanel>
      </CardContent>
    </SurfaceCard>
  );
}
