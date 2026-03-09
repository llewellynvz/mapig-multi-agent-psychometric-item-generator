import { Metadata } from "next";
import EvaluationDashboard from "@/components/EvaluationDashboard";

export const metadata: Metadata = {
  title: "Evaluation Suite | MAPIG",
  description: "System quality evaluation dashboard",
};

export default function EvaluationPage() {
  return (
    <div className="container mx-auto py-8 px-4">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Evaluation Suite</h1>
        <p className="text-slate-400">
          Automated quality evaluation comparing MAPIG-generated items to published scales
        </p>
      </div>

      <EvaluationDashboard />
    </div>
  );
}
