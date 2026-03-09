import fs from "fs";
import path from "path";

const DEBUG_LOG_PATH = path.join(process.cwd(), "..", ".cursor", "debug.log");

// #region agent log
export async function GET() {
  try {
    const dir = path.dirname(DEBUG_LOG_PATH);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    const payload = {
      id: `log_${Date.now()}`,
      timestamp: Date.now(),
      location: "frontend/api/debug-ping/route.ts",
      message: "next_api_hit",
      data: { path: "/api/debug-ping", cwd: process.cwd() },
      hypothesisId: "H1_H2_H4",
    };
    fs.appendFileSync(DEBUG_LOG_PATH, JSON.stringify(payload) + "\n");
  } catch {
    // ignore
  }
  return Response.json({ ok: true });
}
// #endregion
