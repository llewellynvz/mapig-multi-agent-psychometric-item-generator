"use client";

import { Stepper, type StepId } from "@/components/Stepper";

export interface FlowStepperProps {
  current: StepId;
}

export function FlowStepper({ current }: FlowStepperProps) {
  return <Stepper current={current} />;
}
