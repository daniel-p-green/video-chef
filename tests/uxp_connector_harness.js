const fs = require("fs");
const vm = require("vm");

const runtimePath = process.argv[2];
if (!runtimePath) throw new Error("runtime path is required");

class Element {
  constructor() {
    this.value = "";
    this.checked = false;
    this.disabled = false;
    this.textContent = "";
    this.className = "";
    this.listeners = {};
  }
  addEventListener(type, callback) { this.listeners[type] = callback; }
}

const elements = Object.fromEntries(
  ["state", "token", "remember", "connect", "disconnect", "forget"].map(id => [id, new Element()])
);
elements.remember.checked = true;

const item = {
  getName: async () => "Fixture clip",
  getStartTime: async () => ({seconds: 1}),
  getEndTime: async () => ({seconds: 3}),
  getInPoint: async () => ({seconds: 4}),
  getOutPoint: async () => ({seconds: 6}),
  getProjectItem: async () => ({name: "Fixture source", getMediaFilePath: async () => "/fixture/source.mp4"}),
  isDisabled: async () => false
};
const track = mediaType => ({
  id: mediaType === "video" ? 10 : 20,
  name: mediaType === "video" ? "V1" : "A1",
  getTrackItems: () => [item],
  isMuted: async () => false
});
const sequence = {
  name: "Fixture sequence",
  guid: "sequence-guid",
  getEndTime: async () => ({seconds: 12}),
  getFrameSize: async () => ({width: 1920, height: 1080}),
  getTimebase: async () => "8475667200",
  getVideoTrackCount: async () => 1,
  getAudioTrackCount: async () => 1,
  getCaptionTrackCount: async () => 2,
  getVideoTrack: async () => track("video"),
  getAudioTrack: async () => track("audio")
};
const project = {
  name: "Fixture project",
  path: "/fixture/project.prproj",
  guid: "project-guid",
  getActiveSequence: async () => sequence
};

const saved = [];
const results = [];
const requests = [];
const jobs = [
  {id: "job-ping", operation: "ping", payload: {}, protocol_version: "1.0"},
  {id: "job-snapshot", operation: "snapshot_active_sequence", payload: {}, protocol_version: "1.0"}
];
const response = (status, body) => ({
  status,
  ok: status >= 200 && status < 300,
  text: async () => body === null ? "" : JSON.stringify(body)
});

const intervals = [];
const context = {
  AbortController,
  console,
  Date,
  JSON,
  Math,
  Promise,
  String,
  document: {getElementById: id => elements[id]},
  window: {addEventListener: () => {}},
  setTimeout,
  clearTimeout,
  setInterval: callback => { intervals.push(callback); return intervals.length; },
  clearInterval: () => {},
  fetch: async (url, options = {}) => {
    requests.push({url, options});
    if (url.endsWith("/v1/connector/register")) return response(200, {ok: true, mutation_enabled: false});
    if (url.endsWith("/v1/connector/next")) return jobs.length ? response(200, jobs.shift()) : response(204, null);
    if (url.endsWith("/v1/connector/result")) {
      results.push(JSON.parse(options.body));
      return response(200, {ok: true});
    }
    if (url.endsWith("/v1/connector/unregister")) return response(200, {ok: true, removed: true});
    throw new Error(`unexpected URL ${url}`);
  },
  require: name => {
    if (name === "premierepro") {
      return {
        Project: {getActiveProject: async () => project},
        ClipProjectItem: {cast: projectItem => projectItem},
        Constants: {TrackItemType: {CLIP: 1}}
      };
    }
    if (name === "uxp") {
      return {
        host: {version: "26.3.2"},
        storage: {secureStorage: {
          getItem: async () => null,
          setItem: async (key, value) => saved.push({key, value}),
          removeItem: async () => {}
        }}
      };
    }
    throw new Error(`unexpected module ${name}`);
  }
};

async function main() {
  vm.runInNewContext(fs.readFileSync(runtimePath, "utf8"), context, {filename: runtimePath});
  await Promise.resolve();
  elements.token.value = "fixture-token-that-is-long-enough-for-the-bridge";
  await elements.connect.listeners.click();
  if (!elements.connect.disabled || elements.disconnect.disabled) throw new Error("connected controls are incorrect");
  if (saved.length !== 1) throw new Error("token was not stored securely after registration");
  if (results[0].result.data.message !== "pong") throw new Error("ping result was not returned");
  if (results[0].result.data.active_sequence !== "Fixture sequence") throw new Error("ping lacks sequence identity");
  await intervals[0]();
  const snapshot = results[1].result.data;
  if (snapshot.schema_version !== "1.1") throw new Error("snapshot schema mismatch");
  if (snapshot.sequence.caption_track_count !== 2) throw new Error("caption count missing");
  if (snapshot.partial !== false || snapshot.issues.length !== 0) throw new Error("complete snapshot marked partial");
  if (snapshot.tracks[0].items[0].media_path !== "/fixture/source.mp4") throw new Error("media evidence missing");
  const register = requests.find(entry => entry.url.endsWith("/v1/connector/register"));
  const registration = JSON.parse(register.options.body);
  if (!registration.instance_id || registration.connector_version !== "1.2.1") throw new Error("registration identity missing");
  if (!register.options.headers["X-Video-Chef-Connector-ID"]) throw new Error("connector header missing");
  if (!register.url.startsWith("https://localhost:17841/")) throw new Error("connector did not use loopback HTTPS");
  await elements.disconnect.listeners.click();
  if (elements.disconnect.disabled !== true) throw new Error("disconnect controls are incorrect");
  process.stdout.write("UXP connector harness passed\n");
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
