import { Stepper } from "@/components/Stepper";

export default function StepperStoryPage() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-[#0B2A34] via-[#0F3743] to-[#1A4A53] p-6">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        <Stepper current="setup" />
        <Stepper current="run" />
        <Stepper current="results" />
      </div>
    </main>
  );
}

