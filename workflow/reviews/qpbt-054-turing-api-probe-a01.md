# QPBT-054 Turing API probe (A01)

Session: `i054-probe-a01-turing-api`  
External identity: `/root/i054_orchestrator_a01_f06a_contract/i054_probe_a01_turing_api`  
Mode: bounded read-only API and elaboration probe

## Result

The probe found a compiling representation of the F06A dependent query
boundary. Valid previous-marginal prefixes and factor-supported inputs are
subtype carriers; their proof components are erased from the machine input by
projecting `.1`. `Subtype.ext` and proof irrelevance recover query equality
from equality of encoded values.

The same probe validated a real `Turing.FinTM2` boundary,
`Turing.TM2OutputsInTime`, exact executed-step extraction through
`EvalsToInTime.toEvalsTo.steps`, and an injective packing of six logical bit
tapes. It introduced no arbitrary run relation or caller-supplied executable
obligation.

## Authentication And Validation

- Temporary probe: `/tmp/i054_dependent_probe_a01.lean`
- Probe SHA-256:
  `6b07a7070b6dac2983906ecb7284d68095631911d16a2492c18009569cca8c25`
- Command: `lake env lean /tmp/i054_dependent_probe_a01.lean`
- Result: exit 0 in 3.04 seconds against the private pinned Lean environment
- Repository base: `639c883737e07b91156a9cbc31ec1aa65100a935`
- Repository edits, Git writes, network actions, builds, and nested agents: 0
- Token usage: `null`; the collaboration backend exposes no per-agent count

The temporary file contains probe-local `sorry` bodies for definitions outside
this API question. They are not repository artifacts or candidate proof debt.
The QPBT-054 orchestrator must still elaborate and review the complete final
manifest; this probe is supporting evidence, not approval.
