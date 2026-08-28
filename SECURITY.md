# Security and privacy

Video projects often contain unreleased products, personal information, testimony, licensed assets, and sensitive metadata. Video Chef defaults to local, minimal, reversible processing and does not authorize uploads, publication, delivery, purchases, or destructive project changes.

Report security vulnerabilities privately through GitHub's security-advisory feature rather than a public issue. Do not include real private media, credentials, or client data in a report; use a minimal synthetic reproduction.

The included scripts invoke local `ffmpeg`/`ffprobe` and operate on paths supplied by the user. Review commands and destination paths before using them on valuable projects.

The Premiere bridge binds only to `127.0.0.1`, authenticates every request with a randomly generated bearer token stored in a mode-`0600` local config, and accepts only explicit read operations. Do not commit, paste, log, or share that token. The bundled UXP connector cannot mutate projects or timelines. Review any future write-capable bridge as a separate security boundary.
