"use client";

import * as React from "react";

const CHUNK_RELOAD_KEY = "mapig-chunk-reload-once";

function getMessage(reason: unknown): string {
  if (typeof reason === "string") return reason;
  if (reason && typeof reason === "object" && "message" in reason) {
    const message = (reason as { message?: unknown }).message;
    return typeof message === "string" ? message : "";
  }
  return "";
}

function isChunkLoadMessage(message: string): boolean {
  return /ChunkLoadError|Loading chunk .* failed|Failed to fetch dynamically imported module/i.test(message);
}

export function ChunkLoadRecovery() {
  React.useEffect(() => {
    const reloadOnce = () => {
      if (sessionStorage.getItem(CHUNK_RELOAD_KEY) === "1") return;
      sessionStorage.setItem(CHUNK_RELOAD_KEY, "1");
      window.location.reload();
    };

    const clearReloadFlag = () => {
      sessionStorage.removeItem(CHUNK_RELOAD_KEY);
    };

    const onError = (event: ErrorEvent) => {
      const message = getMessage(event.error) || event.message;
      if (isChunkLoadMessage(message)) {
        reloadOnce();
      }
    };

    const onUnhandledRejection = (event: PromiseRejectionEvent) => {
      const message = getMessage(event.reason);
      if (isChunkLoadMessage(message)) {
        event.preventDefault();
        reloadOnce();
      }
    };

    window.addEventListener("load", clearReloadFlag, { once: true });
    window.addEventListener("error", onError);
    window.addEventListener("unhandledrejection", onUnhandledRejection);

    return () => {
      window.removeEventListener("load", clearReloadFlag);
      window.removeEventListener("error", onError);
      window.removeEventListener("unhandledrejection", onUnhandledRejection);
    };
  }, []);

  return null;
}
