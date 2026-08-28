/* Video Chef Premiere Bridge 1.2 — original read-only UXP connector. */
const ppro = require("premierepro");
const uxp = require("uxp");

const ENDPOINT = "https://localhost:17841";
const PROTOCOL_VERSION = "1.0";
const CONNECTOR_VERSION = "1.2.1";
const CAPABILITIES = ["ping", "snapshot_active_sequence"];
const TOKEN_STORAGE_KEY = "video-chef-premiere-bridge-token-v1";
const POLL_INTERVAL_MS = 700;
const REQUEST_TIMEOUT_MS = 5000;
const INSTANCE_ID = `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}-${Math.random().toString(36).slice(2)}`;

let token = "";
let timer = null;
let busy = false;
let connected = false;

const state = document.getElementById("state");
const tokenInput = document.getElementById("token");
const rememberInput = document.getElementById("remember");
const connectButton = document.getElementById("connect");
const disconnectButton = document.getElementById("disconnect");
const forgetButton = document.getElementById("forget");

function setState(message, kind = "") {
  state.textContent = message;
  state.className = `state ${kind}`.trim();
}

function setControls() {
  connectButton.disabled = connected;
  disconnectButton.disabled = !connected;
}

async function bridge(path, options = {}, timeoutMs = REQUEST_TIMEOUT_MS) {
  const headers = Object.assign({}, options.headers || {}, {
    "Authorization": `Bearer ${token}`,
    "Content-Type": "application/json",
    "X-Video-Chef-Connector-ID": INSTANCE_ID
  });
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(`${ENDPOINT}${path}`, Object.assign({}, options, {
      headers,
      signal: controller.signal
    }));
    if (response.status === 204) return null;
    const raw = await response.text();
    let body = {};
    try { body = raw ? JSON.parse(raw) : {}; }
    catch (_) { throw new Error(`Bridge returned invalid JSON (${response.status})`); }
    if (!response.ok) throw new Error(body.error || `Bridge returned ${response.status}`);
    return body;
  } finally {
    clearTimeout(timeout);
  }
}

function asId(value) {
  try { return value.toString(); } catch (_) { return String(value); }
}

function bytesToString(value) {
  if (!value) return "";
  let result = "";
  for (const byte of value) result += String.fromCharCode(byte);
  return result;
}

async function projectItemEvidence(projectItem) {
  if (!projectItem) return {project_item_name: "", media_path: ""};
  let mediaPath = "";
  try {
    const clipProjectItem = ppro.ClipProjectItem.cast(projectItem);
    mediaPath = await clipProjectItem.getMediaFilePath();
  } catch (_) { /* sequence, synthetic item, or unavailable media */ }
  return {project_item_name: projectItem.name || "", media_path: mediaPath || ""};
}

async function itemEvidence(item) {
  const [name, start, end, sourceIn, sourceOut, projectItem, disabled] = await Promise.all([
    item.getName(), item.getStartTime(), item.getEndTime(), item.getInPoint(),
    item.getOutPoint(), item.getProjectItem(), item.isDisabled()
  ]);
  return Object.assign({
    name,
    timeline_start_seconds: start.seconds,
    timeline_end_seconds: end.seconds,
    source_in_seconds: sourceIn.seconds,
    source_out_seconds: sourceOut.seconds,
    disabled: Boolean(disabled)
  }, await projectItemEvidence(projectItem));
}

async function trackEvidence(track, mediaType, index, issues) {
  const items = track.getTrackItems(ppro.Constants.TrackItemType.CLIP, false);
  const evidence = [];
  for (let itemIndex = 0; itemIndex < items.length; itemIndex++) {
    try {
      evidence.push(await itemEvidence(items[itemIndex]));
    } catch (error) {
      issues.push({
        scope: `${mediaType}_track_${index + 1}_item_${itemIndex + 1}`,
        error: String(error)
      });
    }
  }
  evidence.sort((a, b) => a.timeline_start_seconds - b.timeline_start_seconds);
  return {
    media_type: mediaType,
    index,
    id: track.id,
    name: track.name || `${mediaType} ${index + 1}`,
    muted: await track.isMuted(),
    items: evidence
  };
}

async function snapshotActiveSequence() {
  const project = await ppro.Project.getActiveProject();
  if (!project) throw new Error("No active Premiere project");
  const sequence = await project.getActiveSequence();
  if (!sequence) throw new Error("No active Premiere sequence");
  const [end, frame, timebase, videoCount, audioCount, captionCount] = await Promise.all([
    sequence.getEndTime(), sequence.getFrameSize(), sequence.getTimebase(),
    sequence.getVideoTrackCount(), sequence.getAudioTrackCount(), sequence.getCaptionTrackCount()
  ]);
  const tracks = [];
  const issues = [];
  for (let i = 0; i < videoCount; i++) {
    tracks.push(await trackEvidence(await sequence.getVideoTrack(i), "video", i, issues));
  }
  for (let i = 0; i < audioCount; i++) {
    tracks.push(await trackEvidence(await sequence.getAudioTrack(i), "audio", i, issues));
  }
  return {
    schema_version: "1.1",
    captured_at: new Date().toISOString(),
    connector: {version: CONNECTOR_VERSION, mutation_enabled: false},
    project: {name: project.name, path: project.path, guid: asId(project.guid)},
    sequence: {
      name: sequence.name,
      guid: asId(sequence.guid),
      duration_seconds: end.seconds,
      frame_width: frame.width,
      frame_height: frame.height,
      timebase_ticks_per_frame: timebase,
      caption_track_count: captionCount
    },
    partial: issues.length > 0,
    issues,
    tracks
  };
}

async function execute(job) {
  if (job.protocol_version !== PROTOCOL_VERSION) throw new Error("Protocol mismatch");
  if (job.operation === "ping") {
    const project = await ppro.Project.getActiveProject();
    const sequence = project ? await project.getActiveSequence() : null;
    return {
      ok: true,
      data: {
        message: "pong",
        premiere_version: uxp.host.version,
        active_project: project ? project.name : null,
        active_sequence: sequence ? sequence.name : null,
        connector_version: CONNECTOR_VERSION,
        mutation_enabled: false
      }
    };
  }
  if (job.operation === "snapshot_active_sequence") return {ok: true, data: await snapshotActiveSequence()};
  throw new Error(`Operation is not allowlisted: ${job.operation}`);
}

async function poll() {
  if (busy || !token || !connected) return;
  busy = true;
  try {
    const job = await bridge("/v1/connector/next");
    if (job) {
      let result;
      try { result = await execute(job); }
      catch (error) { result = {ok: false, error: String(error)}; }
      await bridge("/v1/connector/result", {
        method: "POST",
        body: JSON.stringify({id: job.id, result})
      });
      setState(`Connected · read-only\nCompleted ${job.operation}`, result.ok ? "ok" : "error");
    }
  } catch (error) {
    connected = false;
    if (timer) clearInterval(timer);
    timer = null;
    setControls();
    setState(`Connection lost\n${error}\nPress Connect to retry.`, "error");
  } finally {
    busy = false;
  }
}

async function connect() {
  token = tokenInput.value.trim();
  if (token.length < 32) {
    setState("Paste the private bridge token first.", "error");
    return;
  }
  connectButton.disabled = true;
  setState("Connecting…");
  try {
    await bridge("/v1/connector/register", {
      method: "POST",
      body: JSON.stringify({
        protocol_version: PROTOCOL_VERSION,
        connector_version: CONNECTOR_VERSION,
        premiere_version: uxp.host.version,
        instance_id: INSTANCE_ID,
        capabilities: CAPABILITIES
      })
    });
    if (rememberInput.checked) await uxp.storage.secureStorage.setItem(TOKEN_STORAGE_KEY, token);
    connected = true;
    if (timer) clearInterval(timer);
    timer = setInterval(poll, POLL_INTERVAL_MS);
    setControls();
    setState(`Connected to ${ENDPOINT}\nPremiere ${uxp.host.version}\nRead-only`, "ok");
    await poll();
  } catch (error) {
    connected = false;
    setControls();
    const detail = String(error);
    const guidance = /permission|certificate|fetch|network/i.test(detail)
      ? "\nRun Video Chef Premiere Bridge doctor, confirm HTTPS trust, then reload this plugin."
      : "";
    setState(`Could not connect\n${detail}${guidance}`, "error");
  }
}

async function disconnect() {
  if (timer) clearInterval(timer);
  timer = null;
  if (connected && token) {
    try {
      await bridge("/v1/connector/unregister", {
        method: "POST",
        body: JSON.stringify({instance_id: INSTANCE_ID})
      }, 2000);
    } catch (_) { /* broker may already be stopped */ }
  }
  connected = false;
  token = "";
  setControls();
  setState("Disconnected");
}

async function forgetToken() {
  await disconnect();
  try { await uxp.storage.secureStorage.removeItem(TOKEN_STORAGE_KEY); } catch (_) { /* key may not exist */ }
  tokenInput.value = "";
  rememberInput.checked = false;
  setState("Disconnected\nSaved token removed.");
}

async function restoreToken() {
  try {
    const saved = bytesToString(await uxp.storage.secureStorage.getItem(TOKEN_STORAGE_KEY));
    if (saved.length >= 32) {
      tokenInput.value = saved;
      rememberInput.checked = true;
      await connect();
    }
  } catch (_) { /* secure storage is a cache; manual paste remains available */ }
}

connectButton.addEventListener("click", connect);
disconnectButton.addEventListener("click", disconnect);
forgetButton.addEventListener("click", forgetToken);
window.addEventListener("unload", () => {
  if (timer) clearInterval(timer);
});

setControls();
restoreToken();
