# Getting Started

1. Install the collection with `ansible-galaxy collection install itsomidkarami.offsitebuddy`, or run from a source checkout with this repository as the working directory.
2. Use Debian-family or UGOS hosts with Docker Compose and systemd.
3. Create an untagged Tailscale auth key for each client-side Tailscale
   sidecar. Cross-tailnet machine shares are accepted by users, and tagged
   machines in the other tailnet cannot access them.
4. Create a quota-managed storage path for each friend.
5. Create a Tailscale auth key for each friend-sidecar device.
6. Put secrets in Ansible Vault.
7. Configure `offsitebuddy_friends` on the server.
8. Run `playbooks/server.yml`.
9. Share the friend-specific Tailscale device manually in the Tailscale admin UI.
   Share only the server-side device; do not mutually share the client device
   for this backup path.
10. Configure `offsitebuddy_client_jobs` on the client. For cross-tailnet
    shares, use the shared server sidecar's Tailnet IP as the repository
    endpoint. A full MagicDNS FQDN (`<hostname>.<server-tailnet>.ts.net`) is
    supported only after it resolves in the generated restic execution path:
    that one-shot container can use Docker's `127.0.0.11` embedded DNS resolver.
    Short hostnames are unsupported. Discover the IP with `tailscale ip -4` in
    the server sidecar, then follow the safe discovery, validation, and
    lifecycle guidance in [Tailnet endpoints](tailnet-endpoints.md). Repository
    credentials must remain Vault-derived and URL-encoded. Add
    `tailscale.hostname` and `tailscale.auth_key` to give the backup job its own
    Tailscale identity. Excludes must be concrete absolute paths, not globs.
11. Run `playbooks/client.yml`.
12. Run a restore test.

OffsiteBuddy does not make an untested backup safe. Restore from the repo before trusting it.
