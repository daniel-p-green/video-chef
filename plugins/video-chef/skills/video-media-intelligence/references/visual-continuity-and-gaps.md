# Visual continuity and gaps

Inspect representative frames to find candidates, then inspect exact ranges used. Check composition, eyeline, action direction, camera movement, exposure, white balance, focus, motion blur, screen readability, cursor state, sensitive data, wardrobe, props, lighting, and temporal continuity.

Start long-form discovery with scene boundaries when cuts or shot changes are meaningful. `../../scripts/scene_detect.py` writes a timestamped scene manifest and can extract one frame per boundary. Scene confidence is a technical signal, not a judgment that a moment matters.

For a reference animation, transition, camera move, or brief visual defect, use `../../scripts/extract_frame_sequence.py` on a short explicit range. Choose an inspection rate high enough to reveal the motion, keep the frame cap in place, and compare positions, scale, rotation, opacity, easing, blur, and hold timing across the sequence. Any inferred curve remains a hypothesis until reproduced and visually compared at normal speed.

Screen recordings require a separate complete-runtime pass. Record each meaningful click, cursor move, typed entry, screen state, readability problem, missing or out-of-order step, script mismatch, and private or unreleased detail in `../../assets/SCREEN_REVIEW.template.csv`. Representative frames cannot prove that the remainder is safe or complete.

Separate an observed defect from a causal hypothesis. A blurry frame may come from focus, motion, scaling, proxy quality, or decode; test before prescribing repair.

Coverage gaps should be classified by consequence: new capture required; alternate take or camera can solve it; existing B-roll or an approved graphic can cover transparently; rights or consent block use; or optional polish only.

Do not generate coverage that could be mistaken for a real product state, participant, place, event, or archival record.
