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
    shares, start with the shared machine FQDN
    `<hostname>.<server-tailnet>.ts.net`, not the short hostname. Some Docker
    hosts keep the one-shot restic container on Docker's `127.0.0.11` embedded
    DNS resolver, where MagicDNS names may not resolve. If restic reports
    `no such host`, use the server sidecar's Tailnet IP in `repository`; find it
    in the Tailscale admin console or with `tailscale ip` inside that sidecar.
    If the repository URL embeds credentials, URL-encoded username and password
    values are required. Add `tailscale.hostname` and `tailscale.auth_key` to
    give the backup job its own Tailscale identity. Excludes must be concrete
    absolute paths, not globs.
11. Run `playbooks/client.yml`.
12. Run a restore test.

OffsiteBuddy does not make an untested backup safe. Restore from the repo before trusting it.
