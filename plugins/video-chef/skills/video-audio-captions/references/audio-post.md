# Audio post

Preserve the original track and document each derived file or effect chain. Diagnose hum, broadband noise, rustle, clipping, reverberation, plosives, sibilance, mouth noise, dropouts, and sync separately.

Prefer clip gain, fades, local spectral repair, room tone, and narrow corrective processing before global denoise or aggressive dynamics. Compare treated and untreated audio at matched loudness. Listen for pumping, chirping, phase change, dullness, lisping, clipped consonants, and unnatural silence.

Build in this order when appropriate: dialogue edit and sync; local repair; dialogue consistency; ambience/room tone; music and SFX; automation/ducking; destination measurement; end-to-end listen.

EBU R 128 recommends programme-loudness and maximum-true-peak measurement for broadcast normalization. FFmpeg's `ebur128` filter reports integrated, momentary, short-term, loudness range, and peak measures. Treat the destination specification as authoritative; FFmpeg's default -23 LUFS reference and its note that online material may use other targets are not universal delivery mandates.

Sources: https://tech.ebu.ch/docs/r/r128.pdf and https://ffmpeg.org/ffmpeg-filters.html#ebur128
