---
name: video-finishing-delivery
description: Conform, restore, color-manage, export, inspect, quality-check, package, and verify professional review files and delivery masters. Use for picture finishing, color, codecs, frame rate, loudness/caption integration, automated QC, masters, and delivery confirmation; do not use to decide an unresolved story.
---

# Video Finishing and Delivery

Finish against a written specification and verify the fresh output. A structurally valid file can still be visually, sonically, editorially, or contractually wrong.

## Workflow

1. Resolve the locked picture, canonical project/sequence, source relink state, effects, graphics, captions, audio mix, color pipeline, and delivery destination.
2. Write or confirm `../../assets/DELIVERY_SPEC.template.md`. Verify destination requirements at delivery time because platform rules can change.
3. Conform full-resolution media and check handles, speed changes, scaling, field order, frame rate, aspect, alpha, color metadata, captions, and audio layout.
4. Prove restoration, reframing, relighting, denoise, identity-affecting work, or color changes on matched source/candidate ranges before full render.
5. Export a review candidate or master to a new explicit path. Wait for the writer to close the file.
6. Run `../../scripts/media_qc.py`, compare results to the delivery specification, and investigate flagged black/frozen intervals rather than assuming they are defects.
7. Watch the entire fresh output at normal speed and intended scale; listen end to end; review captions; inspect matched A/Bs for repaired areas.
8. Complete `../../assets/QA_REPORT.template.md`, obtain owner approval, then deliver only with authorization and confirm the external result separately.

## Hard boundaries

- Preserve the editable master and source media. Separate review proxies, mezzanine masters, platform encodes, and delivered copies.
- Do not normalize frame rate, color, loudness, or dimensions without a destination or project reason.
- Metadata tags do not prove correct color appearance; meters do not prove a good mix; a decode does not prove story or owner approval.
- Do not call a file final based on its filename, export completion, or upload progress.
- Avoid generation-credit or cloud-restoration spend without explicit approval, stated cost, and a bounded proof.

Read [conform-color-restoration.md](references/conform-color-restoration.md) and [qc-and-delivery.md](references/qc-and-delivery.md).
