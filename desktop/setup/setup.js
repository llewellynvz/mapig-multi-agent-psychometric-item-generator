const form = document.getElementById("setup-form");
const statusEl = document.getElementById("status");
const submitBtn = document.getElementById("submitBtn");
const enablePerplexityInput = document.getElementById("enablePerplexity");
const perplexityFields = document.getElementById("perplexityFields");

const openaiApiKeyInput = document.getElementById("openaiApiKey");
const openaiModelInput = document.getElementById("openaiModel");
const perplexityApiKeyInput = document.getElementById("perplexityApiKey");
const perplexityModelInput = document.getElementById("perplexityModel");
const perplexitySearchModeInput = document.getElementById("perplexitySearchMode");
const perplexityMaxResultsInput = document.getElementById("perplexityMaxResults");
const perplexityDomainFilterInput = document.getElementById("perplexityDomainFilter");

const openaiLinkBtn = document.getElementById("openaiLink");
const perplexityLinkBtn = document.getElementById("perplexityLink");

let hasOpenAiKey = false;
let hasPerplexityKey = false;

function setStatus(message, kind = "") {
  statusEl.textContent = message;
  statusEl.className = kind ? `status ${kind}` : "status";
}

function setBusy(isBusy) {
  submitBtn.disabled = isBusy;
  submitBtn.textContent = isBusy ? "Saving and launching..." : "Save and Launch MAPIG";
}

function syncPerplexityVisibility() {
  const enabled = Boolean(enablePerplexityInput.checked);
  perplexityFields.style.display = enabled ? "grid" : "none";
}

function normalizeText(value) {
  return typeof value === "string" ? value.trim() : "";
}

function bindExternalLinks() {
  openaiLinkBtn.addEventListener("click", async () => {
    await window.mapigDesktop.openExternal("https://platform.openai.com/api-keys");
  });
  perplexityLinkBtn.addEventListener("click", async () => {
    await window.mapigDesktop.openExternal("https://www.perplexity.ai/settings/api");
  });
}

async function initialize() {
  bindExternalLinks();
  enablePerplexityInput.addEventListener("change", syncPerplexityVisibility);

  try {
    const state = await window.mapigDesktop.getSetupState();
    hasOpenAiKey = Boolean(state.hasOpenAiKey);
    hasPerplexityKey = Boolean(state.hasPerplexityKey);

    openaiModelInput.value = state.openaiModel ?? "gpt-5-nano";
    enablePerplexityInput.checked = Boolean(state.enablePerplexity);
    perplexityModelInput.value = state.perplexityModel ?? "sonar-pro";
    perplexitySearchModeInput.value = state.perplexitySearchMode ?? "academic";
    perplexityMaxResultsInput.value = String(state.perplexityMaxResults ?? 8);
    perplexityDomainFilterInput.value = state.perplexityDomainFilter ?? "";

    if (hasOpenAiKey) {
      openaiApiKeyInput.placeholder = "Saved key detected. Enter a new key only if you want to replace it.";
    }
    if (hasPerplexityKey) {
      perplexityApiKeyInput.placeholder =
        "Saved key detected. Enter a new key only if you want to replace it.";
    }

    syncPerplexityVisibility();
  } catch (error) {
    setStatus(
      error instanceof Error ? error.message : "Unable to load setup state.",
      "error"
    );
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  setStatus("");

  const payload = {
    openaiApiKey: normalizeText(openaiApiKeyInput.value),
    openaiModel: normalizeText(openaiModelInput.value),
    enablePerplexity: Boolean(enablePerplexityInput.checked),
    perplexityApiKey: normalizeText(perplexityApiKeyInput.value),
    perplexityModel: normalizeText(perplexityModelInput.value),
    perplexitySearchMode: perplexitySearchModeInput.value === "web" ? "web" : "academic",
    perplexityMaxResults: Number(perplexityMaxResultsInput.value),
    perplexityDomainFilter: normalizeText(perplexityDomainFilterInput.value),
  };

  if (!payload.openaiApiKey && !hasOpenAiKey) {
    setStatus("OpenAI API key is required.", "error");
    return;
  }

  if (payload.enablePerplexity && !payload.perplexityApiKey && !hasPerplexityKey) {
    setStatus("Perplexity is enabled but no Perplexity API key was provided.", "error");
    return;
  }

  setBusy(true);
  try {
    const result = await window.mapigDesktop.saveSetupState(payload);
    if (!result?.ok) {
      throw new Error(result?.error || "Could not save settings.");
    }
    setStatus("Launching MAPIG...", "success");
  } catch (error) {
    setStatus(error instanceof Error ? error.message : "Could not save settings.", "error");
    setBusy(false);
  }
});

initialize();

