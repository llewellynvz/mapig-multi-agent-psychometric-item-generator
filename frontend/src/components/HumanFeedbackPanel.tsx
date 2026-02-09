"use client";

import * as React from "react";
import { MessageSquareText, RotateCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
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
    <Card className="border-primary/30 bg-gradient-to-br from-primary/10 via-background to-primary/5 shadow-sm">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base md:text-lg">
          <MessageSquareText className="h-5 w-5 text-primary" />
          Human Feedback Loop
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-muted-foreground">
          Add reviewer guidance and run a refinement pass. The next run uses this feedback plus the current item set as context.
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
        <Button
          type="button"
          onClick={onRefine}
          disabled={isPending || value.trim().length < 8}
          className="w-full sm:w-auto"
        >
          <RotateCw className="mr-2 h-4 w-4" />
          {isPending ? "Refining..." : "Refine with feedback"}
        </Button>
      </CardContent>
    </Card>
  );
}

