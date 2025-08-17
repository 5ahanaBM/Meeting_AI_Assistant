// background.js (Service Worker)

function log(...args) { console.log("[bg]", ...args); }

/**
 * Ensure offscreen document exists.
 */
async function ensureOffscreenDocument() {
  if (!chrome.offscreen?.createDocument) {
    log("offscreen API unavailable");
    throw new Error("offscreen API unavailable");
  }
  const hasDoc = await chrome.offscreen.hasDocument();
  log("has offscreen:", hasDoc);
  if (hasDoc) return;

  await chrome.offscreen.createDocument({
    url: "offscreen.html",
    reasons: [chrome.offscreen.Reason.AUDIO_PLAYBACK],
    justification: "MediaRecorder runs in offscreen to stream tab audio to backend"
  });
  log("created offscreen document");
}

/**
 * Get currently active tab (focused window).
 */
async function getActiveTab() {
  const tabs = await chrome.tabs.query({ active: true, lastFocusedWindow: true });
  if (!tabs || !tabs.length) throw new Error("No active tab");
  return tabs[0];
}

/**
 * Start capture: validate Meet tab, get a tab media stream ID, tell offscreen to start.
 */
async function startCapture(wsUrl) {
  const tab = await getActiveTab();
  log("activeTab:", tab.url);
  if (!tab.url || !tab.url.startsWith("https://meet.google.com/")) {
    throw new Error("Active tab must be a Google Meet tab.");
  }

  // 1) Ensure offscreen exists
  await ensureOffscreenDocument();

  // 2) Get a media stream ID for this tab
  const streamId = await new Promise((resolve, reject) => {
    try {
      chrome.tabCapture.getMediaStreamId({ targetTabId: tab.id }, (id) => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
          return;
        }
        if (!id) {
          reject(new Error("getMediaStreamId returned empty id"));
          return;
        }
        resolve(id);
      });
    } catch (e) {
      reject(e);
    }
  });
  log("media stream id:", streamId);

  // 3) Tell offscreen to start with WS URL and the streamId
  await chrome.runtime.sendMessage({ type: "START", wsUrl, streamId });
}

/**
 * Stop capture.
 */
async function stopCapture() {
  await chrome.runtime.sendMessage({ type: "STOP" });
}

chrome.runtime.onInstalled.addListener(async () => {
  try {
    log("onInstalled fired");
    await ensureOffscreenDocument();
  } catch (e) {
    log("onInstalled ensureOffscreenDocument failed:", e);
  }
});

// Messages from popup
chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  (async () => {
    try {
      log("message:", msg);
      if (msg?.cmd === "START") {
        await startCapture(msg.wsUrl);
        sendResponse({ ok: true });
      } else if (msg?.cmd === "STOP") {
        await stopCapture();
        sendResponse({ ok: true });
      }
    } catch (err) {
      log("error:", err);
      sendResponse({ ok: false, error: String(err) });
    }
  })();
  return true;
});
