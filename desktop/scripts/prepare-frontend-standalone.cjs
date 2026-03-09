const fs = require("fs");
const path = require("path");

const repoRoot = path.resolve(__dirname, "..", "..");
const frontendDir = path.join(repoRoot, "frontend");
const standaloneDir = path.join(frontendDir, ".next", "standalone");
const staticDir = path.join(frontendDir, ".next", "static");
const publicDir = path.join(frontendDir, "public");

function copyDir(source, destination) {
  if (!fs.existsSync(source)) return;
  fs.mkdirSync(destination, { recursive: true });

  for (const entry of fs.readdirSync(source, { withFileTypes: true })) {
    const sourcePath = path.join(source, entry.name);
    const destinationPath = path.join(destination, entry.name);
    if (entry.isDirectory()) {
      copyDir(sourcePath, destinationPath);
    } else {
      fs.copyFileSync(sourcePath, destinationPath);
    }
  }
}

if (!fs.existsSync(path.join(standaloneDir, "server.js"))) {
  throw new Error(
    `Expected standalone server at "${path.join(standaloneDir, "server.js")}". Run frontend build first.`
  );
}

copyDir(staticDir, path.join(standaloneDir, ".next", "static"));
copyDir(publicDir, path.join(standaloneDir, "public"));

console.log("Prepared frontend standalone assets for Electron packaging.");

