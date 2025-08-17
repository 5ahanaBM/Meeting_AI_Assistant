// popup.js
const wsInput = document.getElementById("wsUrl");
const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");

/**
 * Persists the WebSocket URL in extension storage.
 *
 * Args:
 *   url {string}: The WebSocket URL to save.
 *
 * Returns:
 *   Promise<void>
 */
async function saveUrl(url) {
  await chrome.storage.local.set({ wsUrl: url });
}

/**
 * Loads a previously saved WebSocket URL from storage.
 *
 * Returns:
 *   Promise<string>
 */
async function loadUrl() {
  const obj = await chrome.storage.local.get("wsUrl");
  return obj.wsUrl || "ws://127.0.0.1:8000/ws/ingest";
}

/**
 * Initializes popup state and listeners.
 *
 * Returns:
 *   Promise<void>
 */
async function init() {
  wsInput.value = await loadUrl();

  startBtn.addEventListener("click", async () => {
    const url = wsInput.value.trim();
    await saveUrl(url);
    chrome.runtime.sendMessage({ cmd: "START", wsUrl: url }, (resp) => {
      // Optionally handle response in UI
    });
  });

  stopBtn.addEventListener("click", async () => {
    chrome.runtime.sendMessage({ cmd: "STOP" }, (resp) => {
      // Optionally handle response in UI
    });
  });
}

init();
