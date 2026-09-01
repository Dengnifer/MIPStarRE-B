# QPBT-028 OS-isolation scout A03

## Identity

- Session: `i028-scout-a03-os-isolation`
- Role: fresh read-only capability/security scout; not an approving review
- Base commit: `1799fbaf8175157a4aca6841a179fcbd43d7f4ed`
- Base tree: `3f36e74e6b33402142cb9831162a0987ee8f3075`
- Final commit/tree: unchanged
- Worktree: clean; `git diff --check` passed
- Report freeze: `2026-09-01T07:22:33.856886505Z`
- Endpoint/network contacts: 0
- Codex CLI invocations: 0
- Repository edits/commits: 0
- Subagents: 0; topology was one scout under the QPBT-028 orchestrator
- Token usage: `null`; per-session token accounting is not exposed
- Elapsed: use the canonical session lifecycle timer; this child interface did not expose its issuance timestamp, so an honest independent elapsed value is unavailable

## Outcome

Bubblewrap is installed but unusable in this execution environment. Docker is the only locally demonstrated substrate capable of enforcing the required mount, PID, environment, capability, and network namespaces. However, the host does not yet contain a digest-pinned QPBT reviewer image, an internal review network, or the required credential-holding transport broker. Production review must therefore continue to fail closed.

The smallest enforceable production design is a two-container Docker boundary:

1. An evidence/reviewer container receives only the immutable projection and runtime image, has no endpoint credential, and is attached only to a dedicated Docker network marked `Internal=true`.
2. A separately pinned broker container joins that internal network and a narrowly controlled external network. It alone owns the endpoint credential.
3. Before reviewer startup, the broker leases exactly one sandbox source identity and accepts exactly one transport connection. Once Codex establishes that connection, all new connections from the sandbox are rejected. Model-directed descendants cannot open a second broker or external connection.
4. The broker forwards only the authorized normalized endpoint origin and wire API. It never returns or mounts credentials into the reviewer.
5. Any missing or mismatched capability, digest, policy, lease, sentinel test, or second-connection denial prevents command construction and reviewer launch.

An internal network without the one-established-connection broker rule is insufficient: a reviewer shell could otherwise send bytes to the broker itself.

## Observed host facts

### Bubblewrap and namespace probes

- `/home/drx/homebrew/bin/bwrap` resolves to `/home/drx/homebrew/Cellar/bubblewrap/0.11.0/bin/bwrap`.
- Version: `bubblewrap 0.11.0`
- Resolved binary SHA-256: `0b7bb511c4cb7223bf837bfaad9fb04f8989432d04558a681008df42d9a4cd4f`
- Safe independent probe:

```text
bwrap --unshare-all --die-with-parent --ro-bind /usr /usr \
  --proc /proc --dev /dev /usr/bin/true
```

Result:

```text
bwrap: setting up uid map: Operation not permitted
```

Direct probes confirmed the same underlying restriction:

```text
unshare --user --map-root-user /usr/bin/true
unshare --mount /usr/bin/true
unshare --net /usr/bin/true
```

All failed with `Operation not permitted`; the user probe specifically failed writing `/proc/self/uid_map`.

Although `kernel.unprivileged_userns_clone=1` and `user.max_user_namespaces=2147483647`, the current process has:

- `NoNewPrivs: 1`
- empty effective, permitted, ambient, and bounding capability sets
- UID/GID maps limited to one mapped ID

Do not use `--unshare-user-try`: its degradation behavior violates fail-closed isolation.

### Other mechanisms

- `systemd-run` exists, but neither system nor user bus is reachable.
- `firejail`, `nsjail`, `podman`, `systemd-nspawn`, `landlock-restrict`, and `crun` were not found.
- `runc`, `containerd`, and Docker exist.

### Docker

Read-only daemon inspection succeeded:

```text
client=29.2.1 server=29.2.1 api=1.53 os=linux arch=amd64
SecurityOptions=["name=apparmor","name=seccomp,profile=builtin","name=cgroupns"]
```

- Docker CLI SHA-256: `2ed412480e0eca591783f1f81f3ccb1184749a8f6431960e77ada958c7b78db2`
- `runc` SHA-256: `94f4a7051506287b13a2f9e9a143a82643431d796c9c4baf5d5fb1635a9cb2a8`
- The daemon is usable through `/run/docker.sock`.
- No existing network is an attested QPBT internal network.
- No listed image is an attested digest-pinned QPBT Codex reviewer image.
- No container was launched and no image was pulled during this scout.

## Required sandbox policy

The launcher should construct the equivalent of:

```text
docker run --rm --read-only
  --user 65532:65532
  --cap-drop ALL
  --security-opt no-new-privileges=true
  --security-opt seccomp=<exact-reviewed-profile>
  --security-opt apparmor=<exact-reviewed-profile>
  --pids-limit <fixed-limit>
  --memory <fixed-limit>
  --network <attested-internal-review-network>
  --mount type=bind,src=<sealed-projection>,dst=/review,readonly,bind-propagation=rprivate
  --tmpfs /tmp:rw,noexec,nosuid,nodev,size=<fixed-size>
  --workdir /review
  <review-image>@sha256:<authorized-digest>
  env -i PATH=<fixed-image-path> HOME=/nonexistent
    LANG=C.UTF-8 LC_ALL=C.UTF-8
    CODEX_HOME=/run/codex
    <pinned-codex-command>
```

Additional requirements:

- Never mount the source repository, `/home`, host `/tmp`, host `/proc`, user configuration, SSH material, endpoint credentials, or Docker socket.
- Close every non-stdio host descriptor before Docker invocation.
- Use a fresh PID namespace and the container’s own procfs.
- The image must contain a reviewed credential-free Codex configuration.
- Image-defined environment must be audited, then cleared by the entrypoint’s `env -i`.
- Runtime image digest, seccomp digest, AppArmor policy identity, Docker server identity, network identity, broker image/policy digest, and exact launch-argv digest belong in capability attestation.
- The only reviewer network peer is the broker. The broker rejects DNS/proxy tunneling, arbitrary methods/paths, wrong endpoint origins, and every connection after the leased Codex connection.
- Never expose broker or endpoint credentials through environment, files, argv, prompt, result envelope, logs, or reviewer-visible procfs.

## Capability attestation

A production `DockerIsolationCapability` should be created only after all of these pass:

1. Absolute Docker executable, client/server/API versions, daemon OS/arch, and expected executable digest match policy.
2. Daemon reports the required AppArmor, seccomp, and cgroup namespace support.
3. Reviewer and broker images resolve to exact authorized immutable digests; mutable tags are rejected.
4. The named network exists, uses a local bridge, has `Internal=true`, and contains no unrelated peers.
5. Exact seccomp and AppArmor policy digests match.
6. Broker health, endpoint-origin pin, wire-API pin, empty log state, and unused single-connection lease match.
7. An offline disposable sandbox using the exact production flags proves:
   - a randomized unmanifested host sentinel is absent by absolute path;
   - `/proc/1/root`, `/proc/*/fd`, Git alternates, host paths, and Docker socket cannot reach it;
   - only manifest-listed projection files and reviewed runtime files are readable;
   - projection and root filesystem writes fail;
   - environment equals the fixed allowlist and contains no credentials;
   - direct internet and DNS egress fail;
   - the first broker connection succeeds and a descendant/new connection fails.
8. Recursive projection verification and manifest digest verification pass immediately before `docker run`.

Return an opaque process-local capability bound to the exact manifest, image, policies, network, broker lease, and launch argv. Any mismatch burns it. An asserted boolean or mocked production probe is not a capability.

## Offline regression plan

All ordinary unit tests must use injected Docker/broker runners and make no daemon, endpoint, or network contact:

- exact argv, image digest, mounts, security flags, network, and `env -i` allowlist;
- source/sentinel/Docker-socket mounts rejected structurally;
- missing Docker, daemon error, absent security option, mutable image, wrong digest, non-internal network, extra peer, missing broker, or stale lease fails before runner invocation;
- absent or malformed capability cannot cross from offline mode into production;
- environment containing credential and Git-selection variables is not inherited;
- broker test double accepts the leased first stream and rejects second and descendant streams;
- any broker request for a different origin, model, wire API, or unauthorized path fails closed;
- sentinel and projection tampering invalidates the capability;
- all failure paths assert zero endpoint requests and zero credential serialization.

One opt-in local integration test may use the Docker daemon and a preinstalled digest-pinned fixture image. It must use `--network none` or a local fake broker, make no endpoint request, create no persistent container, and verify sentinel denial plus cleanup. The exact same policy builder must serve integration and production; tests must not substitute weaker flags.

## Residual risks

- Docker daemon authority is large; only the trusted outer launcher may access its socket.
- Image runtime files are necessarily visible and must be digest-pinned and independently reviewed.
- A generic internal proxy is not sufficient because descendants could connect to it. The single-established-connection lease and explicit second-connection test are mandatory.
- Codex reconnect behavior must be tested against the broker. If it requires additional connections, production remains disabled until a defensible connection-authentication design exists.
- Container isolation does not authorize content. Version-2 manifest authorization remains an independent prerequisite.
- No real sentinel denial was executed in this read-only scout because the assignment permitted capability inspection only. It is a mandatory implementation/integration gate, not an inferred property from `docker info`.
