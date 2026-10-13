# Public release verification

The release target is 1.9.0. `scripts/verify-publication.py` compares the unauthenticated public index/native build, default Gerber archive, actual mounting drills, review package and pinned GitHub CAD/source bytes against the frozen qualified board. The verified release/version and commit are recorded in `artifacts/publication-verification.json` after publication.

See [engineering fixes](engineering-fixes.md) for current checks. Strict generic Circuit JSON schema and both manufacturing archives pass. No supplier order/process approval, bench qualification or rear motor compatibility is claimed.
