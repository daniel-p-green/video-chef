/* Video Chef Premiere Bridge 1.0 — original read-only UXP connector. */
const ppro = require("premierepro");
const uxp = require("uxp");

const ENDPOINT = "http://127.0.0.1:17841";
const PROTOCOL_VERSION = "1.0";
const CONNECTOR_VERSION = "1.0.0";
const CAPABILITIES = ["ping", "snapshot_active_sequence"];
let token = "";
let timer = null;
let busy = false;

const state = document.getElementById("state");
const tokenInput = document.getElementById("token");

function setState(message, kind = "") {
  state.textContent = message;
  state.className = `state ${kind}`.trim();
}

async function bridge(path, options = {}) {
  const headers = Object.assign({}, options.headers || {}, {
    "Authorization": `Bearer ${token}`,
    "Content-Type": "application/json"
  });
  const response = await fetch(`${ENDPOINT}${path}`, Object.assign({}, options, {headers}));
  if (response.status === 204) return null;
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || `Bridge returned ${response.status}`);
  return body;
}

function asId(value) {
  try { return value.toString(); } catch (_) { return String(value); }
}

async function projectItemEvidence(projectItem) {
  let mediaPath = "";
  try { mediaPath = await projectItem.getMediaFilePath(); } catch (_) { /* sequence or synthetic item */ }
  return { project_item_name: projectItem.name || "", media_path: mediaPath || "" };
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

async function trackEvidence(track, mediaType, index) {
  const items = track.getTrackItems(ppro.Constants.TrackItemType.CLIP, false);
  const evidence = [];
  for (const item of items) evidence.push(await itemEvidence(item));
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
  const [end, frame, timebase, videoCount, audioCount] = await Promise.all([
    sequence.getEndTime(), sequence.getFrameSize(), sequence.getTimebase(),
    sequence.getVideoTrackCount(), sequence.getAudioTrackCount()
  ]);
  const tracks = [];
  for (let i = 0; i < videoCount; i++) tracks.push(await trackEvidence(await sequence.getVideoTrack(i), "video", i));
  for (let i = 0; i < audioCount; i++) tracks.push(await trackEvidence(await sequence.getAudioTrack(i), "audio", i));
  return {
    schema_version: "1.0",
    captured_at: new Date().toISOString(),
    connector: { version: CONNECTOR_VERSION, mutation_enabled: false },
    project: { name: project.name, path: project.path, guid: asId(project.guid) },
    sequence: {
      name: sequence.name,
      guid: asId(sequence.guid),
      duration_seconds: end.seconds,
      frame_width: frame.width,
      frame_height: frame.height,
      timebase_ticks_per_frame: timebase
    },
    tracks
  };
}

async function execute(job) {
  if (job.protocol_version !== PROTOCOL_VERSION) throw new Error("Protocol mismatch");
  if (job.operation === "ping") return {ok: true, data: {message: "pong", mutation_enabled: false}};
  if (job.operation === "snapshot_active_sequence") return {ok: true, data: await snapshotActiveSequence()};
  throw new Error(`Operation is not allowlisted: ${job.operation}`);
}

async function poll() {
  if (busy || !token) return;
  busy = true;
  try {
    const job = await bridge("/v1/connector/next");
    if (job) {
      let result;
      try { result = await execute(job); }
      catch (error) { result = {ok: false, error: String(error)}; }
      await bridge("/v1/connector/result", {method: "POST", body: JSON.stringify({id: job.id, result})});
      setState(`Connected\nCompleted ${job.operation}`, result.ok ? "ok" : "error");
    }
  } catch (error) {
    setState(`Connection error\n${error}`, "error");
  } finally {
    busy = false;
  }
}

async function connect() {
  token = tokenInput.value.trim();
  if (token.length < 32) { setState("Paste the private bridge token first.", "error"); return; }
  try {
    await bridge("/v1/connector/register", {
      method: "POST",
      body: JSON.stringify({
        protocol_version: PROTOCOL_VERSION,
        connector_version: CONNECTOR_VERSION,
        premiere_version: uxp.host.version,
        capabilities: CAPABILITIES
      })
    });
    if (timer) clearInterval(timer);
    timer = setInterval(poll, 700);
    setState(`Connected to ${ENDPOINT}\nPremiere ${uxp.host.version}\nRead-only`, "ok");
  } catch (error) {
    setState(`Could not connect\n${error}`, "error");
  }
}

function disconnect() {
  if (timer) clearInterval(timer);
  timer = null;
  token = "";
  tokenInput.value = "";
  setState("Disconnected");
}

document.getElementById("connect").addEventListener("click", connect);
document.getElementById("disconnect").addEventListener("click", disconnect);
