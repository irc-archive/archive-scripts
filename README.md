# Archival Scripts

This repository contains various scripts for archiving software.

## Tar2Git

Tar2Git takes an archive unpackable with `tar` and converts it to a Git repository.

Usage: tar2git &lt;OUTDIR&gt; &lt;TARBALL&gt; [TARBALL...]

The following environment variables can also be set:

* `T2G_NAME` &mdash; The name to use as the committer.
* `T2G_EMAIL` &mdash; The email to use as the committer.
