# QPBT-040 combined QPBT-014 snapshot validation A01

Session: `i040-orchestrator-a01-combined`

Snapshot: `8d209d6d2b17d96d0f96c2a9b2f95495c57561eb`

Tree: `c234100c01d4b11398e4c098ada6dd28e7e64932`

## Findings

1. **Blocker -- the approved Pauli and Types modules cannot coexist in one
   Lean import environment.**

   `MIPStarRE/QPBT/Basic/Pauli.lean:22-25` and
   `MIPStarRE/QPBT/Game/Types.lean:17-21` each declare unnamed
   `noncomputable local instance`s for `Fintype (GaloisField 2 k)` and
   `DecidableEq (GaloisField 2 k)` in namespace `MIPStarRE.QPBT`. Lean assigns
   the same generated names in both modules, including
   `MIPStarRE.QPBT.instDecidableEqGaloisFieldOfNatNat_mIPStarRE`. Consequently,
   both of these probes fail:

   ```lean
   import MIPStarRE.QPBT.Basic.Pauli
   import MIPStarRE.QPBT.Game.Types
   ```

   ```lean
   import MIPStarRE.QPBT.Game.Types
   import MIPStarRE.QPBT.Basic.Pauli
   ```

   In each order the second import reports that the environment already
   contains the generated declaration from the first module. The four direct
   target builds pass only because no current target imports both modules, and
   the cached `MIPStarRE` aggregate build does not exercise this combined QPBT
   import. This violates QPBT-040's combined-import acceptance gate and blocks
   downstream consumers such as the planned QPBT game, which needs both Pauli
   and typed-sampler APIs.

   The source repair is outside this report-only issue. A child issue should
   give the local instances explicit collision-free names or centralize the
   common instances, then obtain fresh scoped/target/combined-import validation
   and independent review before QPBT-040 is rerun.

No other blocker, high, medium, or low finding was identified.

## Verdict

**Block.** Do not close QPBT-040 or its tracking parent QPBT-014. Candidate
identity, source fidelity, proof-debt boundaries, synchronization, scoped
elaboration, target builds, and the singleton full-build artifact all
authenticate, but the exact integrated snapshot fails its combined import
graph gate. This session owns no Lean or blueprint source and makes no repair.

## Immutable child and integration authentication

All four PR approvals have zero findings and come from sessions distinct from
their implementers/orchestrators. Each candidate commit has one parent. Each
guarded integration records the exact approved candidate as its second parent,
is an ancestor of the validated snapshot, and preserves the candidate Lean
blob through `8d209d6d`.

| PR / node | Approved head (tree; parent) | Approval report SHA-256 | Integration (parents) | Lean blob at head = integration = snapshot | Snapshot file SHA-256 |
| --- | --- | --- | --- | --- | --- |
| LPR-027 / F02 Polynomial | `8467454fefefdbac7478a2df8f8c1e2d9c25fcf5` (`50fec3a3a7611f63aacff2f15568812e123ca29d`; `358cd108db045d13f4e0095a2948dd4037be2b54`) | `24986875977e8e8e5cab4a80a98d66b9c321c102414fe338cf31cdb73106d50e` | `4e003ec80d6bd772530fef854b68dd4ee787906f` (`309973aaccf258b92486e26ce392863ebc1fdb40`, exact head) | `6bf62ea13a192aa08065512275b2bbaa180963e6` | `cb69673911da3c259a822cbb8bc643e38acee18dedec2c808468f78c4d63a05c` |
| LPR-028 / G01 Parameters | `f6b19fc9fb87e0616b8367749ff971539bc1b45f` (`19df34c6a5687eff9bf64611c8880e45b3ea4339`; `874dc07433936e26d62c42cdd779dde42386f99d`) | `ce4f5dc2ec0f7fe56488aac8420693b05678999d2107dbc5a31ed6ae411f017f` | `4a6683795a71712d6a5c52b7539c2f532fd39f71` (`4e003ec80d6bd772530fef854b68dd4ee787906f`, exact head) | `f9d65fc4a468997f93b95cb380d780bce46aed25` | `2f749aca171739bf57d4a7945fbdbdc55bdaf83418a4cabe1a6582520b3ec2e5` |
| LPR-032 / F05-G09 Pauli | `cdb83f4017cfc182eb2611be0fbc5cd3635fbf64` (`239f65b911d5535bdd20bb442c6e9c61aa00f8ff`; `c5f4b277c17c54f2bfff3eb02c1101d4f1e85b60`) | `5e3704296b44bb31729156046bae48268452d30f1c40107fd624cdd649bed818` | `ea2b8877600e737ba5935c42df206236f800efd4` (`fa1c1ca8bb528e6a9715fbd140f5725a67bae657`, exact head) | `d183c3d440bdb49870ba55f8ad06cb029531743e` | `df003a117fb8495bd01bd7ceee45b7c58df5c9e4815bfb4e5a9e344da6b56e12` |
| LPR-036 / F07 Types | `e9fe2bd4747f36d63ec5b3623c5f0c5bda7149cf` (`f7149c6b31db64fe85998f5a0196a90c4ecfafd1`; `937ea218133cc21afb16313076ce2278fbe9260e`) | `ad128311a3ca2849a6af27496a7dcca7a900745f45b039652f8fa279a4443bc4` | `8d209d6d2b17d96d0f96c2a9b2f95495c57561eb` (`445b04c4253e46392d27e9151e212c5ab401e20d`, exact head) | `80d1825c64bbae292f490e677187b2d824fbaedf` | `020b56b3441ee01d1102957f23b65bd0ba6eefcc937eda7f79db78d0bfd32624` |

The LPR-036 candidate and integration binary patches both hash to
`aa23852932f524484c7f443f26cdb83d1b2389c42086ccf61c337f389e3c5442`.
The integration changes exactly `MIPStarRE/QPBT/Game/Types.lean` and
`workflow/reviews/qpbt-058-f07-a01.md` relative to its first parent.

## Snapshot and successor identity

The assigned branch was clean before validation at the exact snapshot and
tree above. The canonical successor
`c6f5032cedfd1b77160487e5acfc83ad39cdac16` changes only workflow state,
metrics, and `workflow/reviews/qpbt-058-postintegration-cache-a10.md`. Its
`MIPStarRE` subtree is byte-identical to the snapshot at tree
`64ea2702fb03ed88e53c340763c6b949b5cfe0f8`.

The following pin/build-recipe blobs are also identical across `8d209d6d` and
`c6f5032`: `lean-toolchain` `94b9f495baff80fd9cb44aad8f4762cb3b2066fe`,
`lakefile.toml` `fc4c0c35d4055fb8c670f1624bc41782710b91b2`,
`lake-manifest.json` `b35f3b125c2e0ec9f3037666898aa0fea5f039d6`,
`references/mipstarre-upstream.json`
`86f0c82ab4d2dfb0da69494f08fd98c88ee8e267`,
`references/lake-packages.json`
`14f49bc82d672709c79de7a5259a528efb51fdd6`, and
`references/mathlib-lake-manifest.json`
`cbd060afa9cc866c4dd286da33b0accf9ecf68ee`.

## Statement integrity

The pinned paper sections were read before evaluating the integrated Lean
statements: `dependencies/low-degree-code.tex:1-94`,
`dependencies/pauli.tex:1-214`, `dependencies/types.tex:1-195`,
`dependencies/conditionally-linear.tex:553-712`, and
`qpbt/qpbt-game-and-soundness.tex:60-63`.

| Lean surface | Paper assumptions | Lean assumptions | Paper conclusion | Lean conclusion | Verdict |
| --- | --- | --- | --- | --- | --- |
| F02 Polynomial | Boolean `y`, field point `x`, and Boolean-indexed field data | `BooleanPoint m`, `FieldPoint k m`, concrete `GaloisField 2 k`; no basis input | Indicator product, linear low-degree encoding, arbitrary-point evaluation, Boolean interpolation | Individually degree-one polynomial subtype, same formulas, linear map, and injectivity from interpolation | exact |
| F05/G09 Pauli | Characteristic-two finite field; scalar/tensor labels and basis choice `X` or `Z` | Concrete `GaloisField 2 k`; finite scalar and `Fin n` tensor indices | X/Z shift and trace phase, product/square, negative twisted phase, genuine eigenprojectors, spectral expansion/inversion | Same scalar/tensor equations, normalization, order, phase, expansion, and inversion; F10 reindexing remains separate | exact |
| F06/F06A Types prefix | Positive indices, admissible field sizes, six-input sampler and four chosen CL query modes; positive level for executable downsize | Odd exponent family, canonical F01 codec, exact six-tape dual-rail encoding, dependent valid queries, genuine executions, intrinsic exponent computation | Associated CL maps and shared-seed law; binary downsize, dimension `s log q`, exact pushforward, global runtime bound | Same callable mathematical/operational boundary; exact distribution/dimension/map laws; compiler existence and runtime proof remain visible Stage-4A debt | faithful boundary |
| F07 Types suffix | Finite graph with loops/orientations, typed CL families, typed downsize and total decider | Nonempty symmetric finite ordered support, constant field-vector sampler carrier, arbitrary dependent decider fibers | Uniform `1/(2m-k)` graph law, typed shared-seed sample, downsized law, total decider | Same ordered-support law and type marginal, graph-preserving pointwise downsize with exact PMF pushforward, total dependent decider; typed machine/runtime remains F07A | faithful boundary |
| G01 Parameters | Natural tuple `(q,m,d)` | Project-owned natural `Parameters`; no LDT alias | Exists odd `k` with `q=2^k` and `m | q`; `d` unconstrained | Exact existential, equality direction, conjunction order, and natural divisibility | exact |

Separate kernel probes for `lowDegreeEncode_injective`,
`pauliTensorProjector_eq_expect_observables`,
`TypeGraph.distribution_apply`, `TypedSampler.sample_types`,
`TypedSampler.sample_downsize`, and `Parameters.Admissible` report only
`propext`, `Classical.choice`, and/or `Quot.sound`, never `sorryAx`.

## Import, debt, and forbidden-assumption audit

The direct imports match the frozen contracts: Polynomial has exactly
`Mathlib.RingTheory.MvPolynomial.Basic` and `MIPStarRE.QPBT.Basic.Field`;
Pauli has exactly its two Mathlib Fourier/character imports, Field, and
Approximation; Types has exactly the three Mathlib computability/log/uniform
imports and Field; Parameters imports only Field. There is no direct import
edge among the four reviewed files, but the combined environment collision in
finding 1 makes the graph unusable.

The exact QPBT source scan finds three materialized holes:

- `MIPStarRE/QPBT/Basic/Field.lean:26`, declaration
  `MIPStarRE.QPBT.fieldDataOfOddExponent`;
- `MIPStarRE/QPBT/Game/Types.lean:1593`, declaration
  `MIPStarRE.QPBT.ExecutableCLSampler.downsizeCompiler_exists`;
- `MIPStarRE/QPBT/Game/Types.lean:1638`, declaration
  `MIPStarRE.QPBT.ExecutableCLSampler.downsize_time`.

All three appear on `blueprint/metadata/nodes.json`'s four-declaration
Stage-4A allowlist. The fourth allowed declaration,
`MIPStarRE.QPBT.pauliSoundness`, is not yet materialized, so the observed debt
is a strict subset of the allowlist. No `admit`, declared `axiom` or
`constant`, `_ofObligations`, generic `Hypotheses`/`Assumptions`, or public
bridge/residual/repair/witness/package/producer input occurs in the four child
files. No unexpected proof debt or forbidden assumption was found.

## Scoped and target validation

All commands ran sequentially in `/tmp/qpbt-040-combined-a01` against its
private writable `.lake`; no full build was invoked by this session.

| Gate | Result | Wall time / jobs |
| --- | --- | --- |
| `lake env lean MIPStarRE/QPBT/Basic/Polynomial.lean` | pass; known lints only | `3.73s` |
| `lake build MIPStarRE.QPBT.Basic.Polynomial` | pass; authorized Field warning and known Polynomial lints | `9.63s`; 2,358 jobs |
| `lake env lean MIPStarRE/QPBT/Basic/Pauli.lean` | pass, no diagnostics | `8.11s` |
| `lake build MIPStarRE.QPBT.Basic.Pauli` | pass; known Approximation lint only | `32.96s`; 8,694 jobs |
| `lake env lean MIPStarRE/QPBT/Game/Types.lean` | pass; two authorized F06A warnings and four unused-variable lints | `10.07s` |
| `lake build MIPStarRE.QPBT.Game.Types` | pass; authorized warnings and known lints | `12.82s`; 3,101 jobs |
| `lake env lean MIPStarRE/QPBT/Game/Parameters.lean` | pass, no diagnostics | `2.42s` |
| `lake build MIPStarRE.QPBT.Game.Parameters` | pass; inherited authorized Field warning | `3.90s`; 2,358 jobs |

The initial Polynomial scoped invocation stopped before elaboration in `2.32s`
because the published cache did not contain the authored `Field.olean`; the
required Polynomial target build populated it. The initial Pauli scoped check
then stopped before elaboration in `1.25s`, and its first target invocation
failed in `2.07s`, because the linked worktree lacked ignored upstream LDT and
Quantum source files. Offline materialization from the authenticated archive
completed in `3.140729s` (`3.20s` process wall), and verification completed in
`0.08s`; the reruns above passed. No source candidate byte changed.

## Blueprint and source synchronization

| Command | Result | Wall time |
| --- | --- | ---: |
| `python3 blueprint/check.py --check` | pass; 54 nodes, 12 chapters, acyclic deterministic outputs | `0.12s` |
| `python3 blueprint/check.py --check --source-root /home/drx/MIPStarRE-auto/references/2001.04383v3` | pass; same declaration graph and pinned sources | `0.13s` |
| `python3 scripts/reference_source.py --reference-root /home/drx/MIPStarRE-auto/references/2001.04383v3 verify` | pass; 39 files, 646 labels | `0.15s` |

The reference inventory is
`04548808c30c476e9b2b7cb2f728a6d0c348a6706a8ed1bc9fb9945f20a124f4`.

## Singleton cache and full-build authentication

The exact recipe-v7 cache key is
`21a7b15fd273fef0829d2ef790f152e6e0af02d4ba75a905e0583a758bcac187`.
Seeding with the prescribed offline Mathlib, MIPStarRE, and Lake-package
archives returned a cache hit, zero miss, zero lock wait (`0.0s`), and zero
builds. It copied 124,925 files, 3 symlinks, and 10,097,592,794 bytes into the
private worktree in `76.217859s` (`76.73s` process wall); source and destination
build directories have distinct device/inode identities and no writable build
output is shared.

The existing singleton manifest authenticates:

- manifest SHA-256
  `4a0f4a6de6c8c3bc25a513c3ac2f4405be2c9704a38af70607a1fdda48fc469d`;
- READY content equal to that digest and READY-file SHA-256
  `784c553af80d2631ecf93049b3f484ec98f6292d9c42a9c7ec5d4e0c7d3d6b4c`;
- build-log SHA-256
  `fce61f45f25031182476b7c769e3460c5059b9a842081d73d96ea3ebe4cf937c`
  (407 lines, 39,503 bytes), ending exactly
  `Build completed successfully (8992 jobs).`;
- full-build duration `643.598163s`, manifest preparation duration
  `750.829030s`, and recorded end-to-end warm duration `772.899268s`;
- one elected builder, zero duplicate builders, and lock wait `0.0s`;
- artifact inventory 124,925 files, 4,147 directories, 3 symlinks,
  10,097,592,794 bytes, digest
  `bc7a64236d2fa7dc1625a7304f525270954e1bc3076ebb0777f93917c28b9590`;
- authored QPBT inventory 7 files, 188,846 bytes, digest
  `4c04b235008352b5690f648aba18e4c61a569ac37304bd0846923b17ca75a254`.

The seed operation recomputed and matched the published artifact inventory;
the offline source verifier matched 337 files, 5,970,111 bytes, source commit
`507e81220d95266ff3d589d125b2f87c7300a9fb`, and inventory digest
`d8d9e7632f5dcdb0cbe7bceeb55c71a0dbbcf6f901c6efd7f4c4814090d096db`.
This session performed no warm, publication, or second full build.

## Accounting

- Topology: `/root` -> `/root/i040_orchestrator_a01_combined`; nested agents:
  `0`.
- Passing scoped Lean checks: `4`; pre-elaboration substrate stops: `2`;
  additional kernel/import probes: `7` process invocations.
- Passing requested target builds: `4`; failed pre-materialization target
  attempts: `1`; full-build invocations/compilations by this session: `0/0`.
- Cache actions: seed `1` (hit `1`, miss `0`, builds `0`, publications `0`,
  lock wait `0.0s`); source materializations `1`; source verifications `1`.
- Findings: `1` blocker; proof retries: `0`; protocol changes: `0`.
- Repository writes: this report only. Canonical state, metrics, protocol,
  source, pin, endpoint, GitHub, credential, network, and nested-agent actions:
  `0`.
- Token usage: `null`; reason: the collaboration backend does not expose
  per-agent token usage, and no estimate is made.
- Exact authoritative session elapsed: `null`; reason: the collaboration
  backend exposes command timings but not a per-agent session wall clock.
