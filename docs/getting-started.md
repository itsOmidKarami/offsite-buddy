# Getting Started

1. Use Debian-family or UGOS hosts with Docker Compose and systemd.
2. Tailscale must be running on the client host so restic containers can reach the friend-specific Tailscale hostname.
3. Create a quota-managed storage path for each friend.
4. Create a Tailscale auth key for each friend-sidecar device.
5. Put secrets in Ansible Vault.
6. Configure `offsitebuddy_friends` on the server.
7. Run `playbooks/server.yml`.
8. Share the friend-specific Tailscale device manually in the Tailscale admin UI.
9. Configure `offsitebuddy_client_jobs` on the client.
10. Run `playbooks/client.yml`.
11. Run a restore test.

OffsiteBuddy does not make an untested backup safe. Restore from the repo before trusting it.
