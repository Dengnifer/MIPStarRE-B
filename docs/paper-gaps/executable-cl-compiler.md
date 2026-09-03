# Executable CL downsizing compiler debt

Tracking: `G19`, `QPBT-060`, and proof-completion issue `QPBT-061`.

## Paper claim

Definition `def:downsize_sampler` in
`conditionally-linear.tex:628-660` defines a downsized Turing machine by four
query cases. Lemma `lem:downsize_sampler` in lines 662-712 states that this
machine has dimension `s(n) log q(n)`, the downsized associated CL functions,
and runtime `O(TIME_S(n) log q(n))`. The proof says only that factor indicators
take an additional `O(log q(n))` output factor.

The paper's Turing-machine convention in `preliminaries.tex:96-143` permits
efficient subroutine simulation and fixes a linear dual-rail tuple encoding.
It also requires the total time to include input encoding, simulation, and
writing the final output.

## Formal obstruction

An admissible field family permits an arbitrary odd exponent function `k(n)`
with `q(n) = 2^k(n)`, while the downsized machine must determine `k(n)` from
the index in order to parse field elements, compute the output dimension, and
expand each selected factor coordinate into an ordered block of `k(n)` bits.
The source supplies no exponent program and does not explicitly charge that
computation to `TIME_S(n)`. This is the existing paper gap `G19`.

The faithful Lean boundary therefore stores a concrete intrinsic
`FieldExponentProgram` in each `ExecutableCLSampler` and defines `time` as the
maximum of its execution cost and the finite maximum over valid sampler
queries. It does not assert that every arbitrary admissible field family has
an executable realization.

## Stage-4A boundary

The complete skeleton permits exactly two F06A theorem-body holes:

- private `MIPStarRE.QPBT.ExecutableCLSampler.downsizeCompiler_exists`, which
  constructs the dual-rail parser, four query compilers/executions, downsized
  decomposition, and binary exponent-program witness;
- public `MIPStarRE.QPBT.ExecutableCLSampler.downsize_time`, which proves the
  paper-labelled global-positive `RuntimeBigO` bound.

The private existence theorem is implementation machinery, not a new paper
theorem and not one of the frozen 56 public names. The definition
`ExecutableCLSampler.downsize` must select from that theorem and contain no
`sorry`. The public theorems `downsize_dimension`, `downsize_associated`, and
`sample_downsize` must be proved at Stage 4A. No axiom, constant, arbitrary
implication input, obligation premise, bridge, package, producer, or public
assumption may stand in for either proof.

## Stage-4C discharge

QPBT-061 must replace both exact holes with proofs. Its compiler proof must
cover dual-rail parsing and tape-boundary preservation, prefix inversion,
simulation of all four canonical queries, ordered factor-block expansion,
intrinsic binary exponent computation, exact execution witnesses, and the
resource inequalities needed for the global-positive runtime theorem. The
proof-complete gate remains zero `sorry`/`admit`/`axiom`/`constant` debt.

This note records missing operational and resource reasoning only. It does not
weaken the source-facing `downsize_time` statement or authorize a conditional
replacement for it.
