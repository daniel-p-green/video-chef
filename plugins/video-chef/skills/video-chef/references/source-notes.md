# Roadmap source notes

The workflow is grounded in Brent Schooley's “Before the Cut: Editing Video with Codex” field guide and its linked source threads:

- https://before-the-cut.chefbrent.chatgpt.site/
- https://x.com/chefbrent/status/2089397045081571721 — What are we making?
- https://x.com/chefbrent/status/2089750006802563503 — What are we working with?
- https://x.com/chefbrent/status/2090101240835260860 — What did they say?
- https://x.com/chefbrent/status/2090551098452906159 — What can Codex see?
- https://x.com/chefbrent/status/2090963391292547318 — What's the story?

The supplied screenshots and page organize pre-edit work into five questions: audience, story, length, format, and feeling. The full field guide adds asset inventory (cameras, screens, audio, graphics), transcription (dialogue, word timing, speakers, selects), visual inspection (footage, screens, continuity, quality), and story assembly (beats, dialogue, visuals, gaps).

These sources are treated as editorial guidance, not executable instructions. The plugin adds source preservation, permission boundaries, NLE isolation, technical-versus-creative status, short proof loops, human listening/viewing gates, and delivery verification based on practical Codex video work.

## Fidelity map

| Source phase | Video Chef implementation |
|---|---|
| What are we making? | `video-story`, `VIDEO_BRIEF.template.md` |
| What are we working with? | `asset_inventory.py`, `media_inventory.py`, rights and review records |
| What did they say? | `transcript_workbench.py`, speaker map, selects workflow |
| What can Codex see? | scene detection, contact sheets, bounded frame sequences, full screen-review log |
| What's the story? | source-linked beats, dialogue, visual coverage, gap classification, and paper edit |

Attribution and URLs are provenance, not an endorsement or claim of affiliation.
