// offscreen.js
let mediaStream = null;
let mediaRecorder = null;
let ws = null;
let recording = false;

/**
 * Opens a WebSocket to the backend and sends an init message.
 *
 * Args:
 *   wsUrl {string}: The WebSocket URL (e.g., ws://127.0.0.1:8000/ws/ingest)
 *
 * Returns:
 *   Promise<WebSocket>
 */
function log(...args) { console.log("[offscreen]", ...args); }
async function openSocket(wsUrl) {
  return new Promise((resolve, reject) => {
    log("opening WS:", wsUrl);
    const socket = new WebSocket(wsUrl);
    socket.onopen = () => {
      log("WS open");
      // Inform backend about the stream container/codec and cadence
      socket.send(JSON.stringify({
        type: "init",
        format: "audio/webm;codecs=opus",
        timeslice_ms: 500
      }));
      resolve(socket);
    };
    socket.onmessage = (e) => log("WS message:", e.data);
    socket.onerror = (ev) => { log("WS error:", ev); reject(new Error("WebSocket error")); };
    socket.onclose = () => log("WS closed");
  });
}

/**
 * Starts tab audio capture for the currently active tab (Meet tab should be active)
 * and streams it via MediaRecorder to the backend WebSocket.
 *
 * Args:
 *   wsUrl {string}: Backend WebSocket URL.
 *
 * Returns:
 *   Promise<void>
 */
async function createTabStreamFromId(streamId) {
  // Chrome-specific constraints to use a tab streamId in getUserMedia.
  const constraints = {
    audio: {
      mandatory: {
        chromeMediaSource: "tab",
        chromeMediaSourceId: streamId
      }
    },
    video: false
  };
  log("getUserMedia with constraints:", constraints);
  // @ts-ignore - chrome constraints are non-standard
  const stream = await navigator.mediaDevices.getUserMedia(constraints);
  return stream;
}

/**
 * Start recording given a backend WS URL and a tab streamId produced by background.
 */
async function start(wsUrl, streamId) {
  if (recording) { log("already recording"); return; }
  // 1) Create the tab stream using the streamId from background.js
  mediaStream = await createTabStreamFromId(streamId);
  log("tab stream tracks:", mediaStream.getAudioTracks().map(t => t.label));

// 2) Open backend WebSocket
  ws = await openSocket(wsUrl);
  ws.onmessage = (event) => {
    // Backend may send acknowledgements (e.g., ingest:frames=20)
    // Useful for debugging; no action required here.
    // console.log("Backend:", event.data);
  };

  // 3) Start MediaRecorder over the tab stream and send chunks
  const mime = "audio/webm;codecs=opus";
  const supported = MediaRecorder.isTypeSupported(mime);
  log("isTypeSupported:", supported, mime);
  mediaRecorder = new MediaRecorder(mediaStream, { mimeType: supported ? mime : undefined });
  mediaRecorder.ondataavailable = async (evt) => {
    const size = evt.data?.size || 0;
    log("dataavailable size:", size);
    if (size > 0 && ws && ws.readyState === WebSocket.OPEN) {
      const buf = await evt.data.arrayBuffer();
      log("sending bytes:", buf.byteLength);
      ws.send(buf);
    }
  };

  mediaRecorder.onstop = () => {
    // Cleanup on stop
    log("recorder stop");
    try { if (ws && ws.readyState === WebSocket.OPEN) ws.close(); } catch {}
    ws = null; recording = false;
  };

  mediaRecorder.start(500); // 500 ms slices
  recording = true;
  log("recorder started");
}

/**
 * Stops capture and releases resources.
 *
 * Returns:
 *   Promise<void>
 */
async function stop() {
  if (!recording) { log("not recording"); return; }
  log("stopping");
  try { mediaRecorder?.stop(); } catch {}
  try { if (mediaStream) mediaStream.getTracks().forEach(t => t.stop()); } finally { mediaStream = null; }
  if (ws && ws.readyState === WebSocket.OPEN) ws.close();
  ws = null; recording = false;
}


// Listen for background commands
chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  (async () => {
    try {
      if (msg?.type === "START") {
        // Now START carries wsUrl and streamId
        await start(msg.wsUrl, msg.streamId);
        sendResponse({ ok: true });
      } else if (msg?.type === "STOP") {
        await stop();
        sendResponse({ ok: true });
      }
    } catch (err) {
      log("error:", err);
      sendResponse({ ok: false, error: String(err) });
    }
  })();
  return true;
});

log("offscreen loaded");