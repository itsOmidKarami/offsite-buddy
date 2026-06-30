# Getting Started

1. Create a quota-managed storage path for each friend.
2. Create a Tailscale auth key for each friend-sidecar device.
3. Put secrets in Ansible Vault.
4. Configure `offsitebuddy_friends` on the server.
5. Run `playbooks/server.yml`.
6. Share the friend-specific Tailscale device manually in the Tailscale admin UI.
7. Configure `offsitebuddy_client_jobs` on the client.
8. Run `playbooks/client.yml`.
9. Run a restore test.

OffsiteBuddy does not make an untested backup safe. Restore from the repo before trusting it.
