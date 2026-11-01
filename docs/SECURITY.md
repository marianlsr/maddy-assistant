# Security and privacy notes

This repository was prepared from a **selected portion** of a private project.
It deliberately excludes private credentials, conversations, account details,
data directories, binary models, and personal home automation settings.

**No static review is a guarantee that a repository has no secrets.** The
owner should independently inspect every file before changing the repository
visibility to Public, and scan it with a trusted secret-scanning tool.

The standalone demo has no network access or external integrations. Workspace
files are written only within a dedicated temporary folder. The tool's path
validation blocks absolute paths, traversal, hidden/config paths, Windows drive
paths and backslash-based paths. It is not designed as an internet-facing sandbox.

If a real credential was ever committed elsewhere in Git history, deleting the
file or adding `.gitignore` is **not enough**. Rotate the affected credential
and remove the exposed history before publication.
