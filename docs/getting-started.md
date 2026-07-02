# Getting Started

1. Install the collection with `ansible-galaxy collection install itsomidkarami.backup`, or run from a source checkout with this repository as the working directory.
2. Use Debian-family or UGOS hosts with Docker Compose and systemd.
3. Tailscale must be running on the client host so restic containers can reach the friend-specific Tailscale hostname.
4. Create a quota-managed storage path for each friend.
5. Create a Tailscale auth key for each friend-sidecar device.
6. Put secrets in Ansible Vault.
7. Configure `offsitebuddy_friends` on the server.
8. Run `playbooks/server.yml`.
9. Share the friend-specific Tailscale device manually in the Tailscale admin UI.
10. Configure `offsitebuddy_client_jobs` on the client. If the repository URL embeds credentials, URL-encoded username and password values are required. Excludes must be concrete absolute paths, not globs.
11. Run `playbooks/client.yml`.
12. Run a restore test.

OffsiteBuddy does not make an untested backup safe. Restore from the repo before trusting it.
