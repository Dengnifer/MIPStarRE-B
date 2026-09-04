#!/usr/bin/env python3
"""Validate and deterministically render the QPBT blueprint graph."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
CHAPTERS = tuple(f"{i:02d}" for i in range(1, 13))
STATUSES = {"not-started", "statement", "proved", "paper-gap"}
FIDELITIES = {"exact", "faithful-boundary", "repaired-internal", "external-boundary"}
KINDS = {"definition", "theorem", "lemma", "corollary", "internal-lemma", "external-theorem"}
RESOLVED_EXTERNAL_STATUSES = {"pinned", "pinned-published"}
EXTERNAL_KEYS = {"id", "arxiv", "version", "url", "role", "treatment", "status"}
PIN_CONTRACT_KEYS = {
    "authority", "versioned_id", "metadata_url", "source_url", "last_revised",
    "release", "verification_basis",
}
AUTHORITATIVE_EXTERNAL_SOURCES = {
    "EXT-TENSOR": {
        "id": "EXT-TENSOR",
        "arxiv": "2111.08131v3",
        "version": "v3",
        "url": "https://arxiv.org/abs/2111.08131v3",
        "status": "pinned-published",
        "pin_contract": {
            "authority": "arXiv",
            "versioned_id": "2111.08131v3",
            "metadata_url": "https://arxiv.org/abs/2111.08131v3",
            "source_url": "https://arxiv.org/src/2111.08131v3",
            "last_revised": "2022-12-06",
            "release": "published-version",
            "verification_basis": "official arXiv metadata",
        },
    },
}
REQUIRED_NODE_KEYS = {
    "id", "chapter", "title", "kind", "public", "status", "fidelity",
    "source", "statement", "lean", "transitive_definitions", "prerequisites",
    "encoding", "boundary_hypotheses", "gap_ids", "integrity",
}
SOURCE_KEYS = {"path", "label", "generated_lines", "original_lines"}
IMPLEMENTATION_CONTRACT_KEYS = {
    "writer_lane", "owned_file", "imports", "signature_manifest", "reused_api",
    "validation_commands", "allowed_minimal_sorries", "proof_complete_sorry_count",
}
IMPLEMENTATION_WRITER_LANES = {
    "field", "approximation", "polynomial", "pauli", "types", "parameters", "game",
}
SIGNATURE_MANIFEST_KEYS = {"path", "begin_marker", "end_marker", "sha256"}
GAME_SEMANTICS_OWNER_ID = "F04A-GAME-SEMANTICS"
GAME_SEMANTICS_SOURCE_ANCHORS = [
    {
        "path": "references/2001.04383v3/sections/dependencies/strategies-distance.tex",
        "label": "def:game",
        "generated_lines": [4, 51],
        "original_lines": [2887, 2934],
    },
    {
        "path": "references/2001.04383v3/sections/dependencies/strategies-distance.tex",
        "label": "def:projective-strategy",
        "generated_lines": [62, 81],
        "original_lines": [2945, 2964],
    },
    {
        "path": "references/2001.04383v3/sections/dependencies/strategies-distance.tex",
        "label": "def:comm-strategy",
        "generated_lines": [126, 190],
        "original_lines": [3009, 3073],
    },
]
GAME_SEMANTICS_PREREQUISITES = ["F04-CONSISTENCY"]
GAME_SEMANTICS_LEAN_NAMES = [
    "MIPStarRE.QPBT.FiniteGame",
    "MIPStarRE.QPBT.FiniteGameStrategy",
    "MIPStarRE.QPBT.strategyValue",
    "MIPStarRE.QPBT.StrategyWinsWithProbability",
    "MIPStarRE.QPBT.FiniteDimensionalGameStrategy",
    "MIPStarRE.QPBT.FiniteDimensionalGameStrategy.value",
    "MIPStarRE.QPBT.gameValue",
    "MIPStarRE.QPBT.ProjectiveStrategy",
    "MIPStarRE.QPBT.SymmetricGame",
    "MIPStarRE.QPBT.SymmetricStrategy",
    "MIPStarRE.QPBT.SupportCommutingStrategy",
    "MIPStarRE.QPBT.ConsistentStrategy",
    "MIPStarRE.QPBT.PCCStrategy",
    "MIPStarRE.QPBT.SPCCStrategy",
    "MIPStarRE.QPBT.schmidtRank",
    "MIPStarRE.QPBT.FiniteDimensionalGameStrategy.schmidtRank",
    "MIPStarRE.QPBT.entanglementRequirement",
    "MIPStarRE.QPBT.HasValueOnePCCStrategy",
]
TYPED_SOURCE_ANCHOR = {
    "path": "references/2001.04383v3/sections/dependencies/types.tex",
    "label": "def:typed-sampler",
    "generated_lines": [57, 195],
    "original_lines": [3623, 3761],
}
TYPED_LEAN_NAMES = [
    "MIPStarRE.QPBT.TypeGraph",
    "MIPStarRE.QPBT.TypeGraph.distribution",
    "MIPStarRE.QPBT.TypeGraph.distribution_apply",
    "MIPStarRE.QPBT.TypedQuestion",
    "MIPStarRE.QPBT.TypedSampler",
    "MIPStarRE.QPBT.TypedSampler.sample",
    "MIPStarRE.QPBT.TypedSampler.sample_types",
    "MIPStarRE.QPBT.TypedSampler.downsize",
    "MIPStarRE.QPBT.TypedSampler.sample_downsize",
    "MIPStarRE.QPBT.TypedDecider",
    "MIPStarRE.QPBT.TypedDecider.accepts",
]
F06_SOURCE_ANCHOR = {
    "path": "references/2001.04383v3/sections/dependencies/conditionally-linear.tex",
    "label": "sec:linear",
    "generated_lines": [1, 552],
    "original_lines": [2163, 2714],
}
F06_EXECUTABLE_OWNER_TERMS = (
    "f06 ends at conditionally-linear.tex:552",
    "f06a-executable-cl alone owns",
    "binary-string representation",
    "six-input",
    "marginal",
    "linear",
    "factor",
    "associated sampler distribution and step count",
    "executable downsizing",
    "s(n) * log q(n)",
    "o(time_s(n) log q(n))",
    "global positive-index runtimebigo",
    "valid-query finite maximum",
    "canonical blank normalization",
    "conditionally-linear.tex:553-712",
    "f07a-detyping, qpbt-043, k03, and k04 own none",
)
EXECUTABLE_CL_OWNER_ID = "F06A-EXECUTABLE-CL"
EXECUTABLE_CL_SOURCE_ANCHORS = [
    {
        "path": "references/2001.04383v3/sections/dependencies/conditionally-linear.tex",
        "label": "def:sampler",
        "generated_lines": [553, 615],
        "original_lines": [2715, 2777],
    },
    {
        "path": "references/2001.04383v3/sections/dependencies/conditionally-linear.tex",
        "label": "lem:cl-kth",
        "generated_lines": [150, 281],
        "original_lines": [2312, 2443],
    },
    {
        "path": "references/2001.04383v3/sections/dependencies/conditionally-linear.tex",
        "label": "lem:cl-downsize",
        "generated_lines": [409, 430],
        "original_lines": [2571, 2592],
    },
    {
        "path": "references/2001.04383v3/sections/dependencies/conditionally-linear.tex",
        "label": "def:sampler-sample",
        "generated_lines": [616, 626],
        "original_lines": [2778, 2788],
    },
    {
        "path": "references/2001.04383v3/sections/dependencies/conditionally-linear.tex",
        "label": "def:downsize_sampler",
        "generated_lines": [628, 660],
        "original_lines": [2790, 2822],
    },
    {
        "path": "references/2001.04383v3/sections/dependencies/conditionally-linear.tex",
        "label": "lem:downsize_sampler",
        "generated_lines": [662, 712],
        "original_lines": [2824, 2874],
    },
    {
        "path": "references/2001.04383v3/sections/top-level/preliminaries.tex",
        "label": "sec:prelim",
        "generated_lines": [1, 35],
        "original_lines": [898, 932],
    },
    {
        "path": "references/2001.04383v3/sections/top-level/preliminaries.tex",
        "label": "sec:tms",
        "generated_lines": [37, 95],
        "original_lines": [934, 992],
    },
    {
        "path": "references/2001.04383v3/sections/top-level/preliminaries.tex",
        "label": "thm:universal-tm",
        "generated_lines": [96, 143],
        "original_lines": [993, 1040],
    },
    {
        "path": "references/2001.04383v3/sections/dependencies/finite-fields.tex",
        "label": "sec:ff-representations",
        "generated_lines": [234, 263],
        "original_lines": [1550, 1579],
    },
    {
        "path": "references/2001.04383v3/sections/dependencies/finite-fields.tex",
        "label": "lem:efficient_basis",
        "generated_lines": [283, 307],
        "original_lines": [1599, 1623],
    },
    {
        "path": "references/2001.04383v3/sections/dependencies/finite-fields.tex",
        "label": "lem:efficient_arithmetic",
        "generated_lines": [350, 401],
        "original_lines": [1666, 1717],
    },
    {
        "path": "references/2001.04383v3/sections/dependencies/finite-fields.tex",
        "label": "rmk:tm_fields",
        "generated_lines": [403, 411],
        "original_lines": [1719, 1727],
    },
]
EXECUTABLE_CL_PREREQUISITES = ["F06-CL"]
EXECUTABLE_CL_LEAN_NAMES = [
    "MIPStarRE.QPBT.AdmissibleFieldFamily",
    "MIPStarRE.QPBT.AdmissibleFieldFamily.fieldSize",
    "MIPStarRE.QPBT.AdmissibleFieldFamily.fieldData",
    "MIPStarRE.QPBT.AdmissibleFieldFamily.fieldCodec",
    "MIPStarRE.QPBT.binaryFieldFamily",
    "MIPStarRE.QPBT.RuntimeBigO",
    "MIPStarRE.QPBT.SixTapeInput",
    "MIPStarRE.QPBT.SixTapeInput.ofLists",
    "MIPStarRE.QPBT.fieldExponentInput",
    "MIPStarRE.QPBT.CLStage.pred",
    "MIPStarRE.QPBT.CLStage.castLE",
    "MIPStarRE.QPBT.CLStage.last",
    "MIPStarRE.QPBT.CLSamplerSide",
    "MIPStarRE.QPBT.CLSamplerSide.bits",
    "MIPStarRE.QPBT.CLSampler.side",
    "MIPStarRE.QPBT.CLPrefix",
    "MIPStarRE.QPBT.CLFactorInput",
    "MIPStarRE.QPBT.CLQueryDecomposition",
    "MIPStarRE.QPBT.CLSamplerQuery",
    "MIPStarRE.QPBT.CLSamplerQuery.instFintype",
    "MIPStarRE.QPBT.CLSamplerQuery.index",
    "MIPStarRE.QPBT.CLSamplerQuery.canonicalTapes",
    "MIPStarRE.QPBT.CLSamplerQuery.expectedOutput",
    "MIPStarRE.QPBT.packSixTapes",
    "MIPStarRE.QPBT.packSixTapes_injective",
    "MIPStarRE.QPBT.IndexedSixInputBitMachine",
    "MIPStarRE.QPBT.IndexedSixInputBitMachine.outputsInTime",
    "MIPStarRE.QPBT.IndexedSixInputBitMachine.Execution",
    "MIPStarRE.QPBT.IndexedSixInputBitMachine.Execution.runInTime",
    "MIPStarRE.QPBT.IndexedSixInputBitMachine.Execution.steps",
    "MIPStarRE.QPBT.FieldExponentProgram",
    "MIPStarRE.QPBT.FieldExponentProgram.machine",
    "MIPStarRE.QPBT.FieldExponentProgram.execution",
    "MIPStarRE.QPBT.FieldExponentProgram.correct",
    "MIPStarRE.QPBT.FieldExponentProgram.steps",
    "MIPStarRE.QPBT.ExecutableCLSampler",
    "MIPStarRE.QPBT.ExecutableCLSampler.associated",
    "MIPStarRE.QPBT.ExecutableCLSampler.decomposition",
    "MIPStarRE.QPBT.ExecutableCLSampler.machine",
    "MIPStarRE.QPBT.ExecutableCLSampler.execution",
    "MIPStarRE.QPBT.ExecutableCLSampler.fieldProgram",
    "MIPStarRE.QPBT.ExecutableCLSampler.correct",
    "MIPStarRE.QPBT.ExecutableCLSampler.executedSteps",
    "MIPStarRE.QPBT.ExecutableCLSampler.validQueries",
    "MIPStarRE.QPBT.ExecutableCLSampler.queryTime",
    "MIPStarRE.QPBT.ExecutableCLSampler.queryTime_eq_validQueryMax",
    "MIPStarRE.QPBT.ExecutableCLSampler.time",
    "MIPStarRE.QPBT.ExecutableCLSampler.time_eq_max",
    "MIPStarRE.QPBT.ExecutableCLSampler.sample",
    "MIPStarRE.QPBT.ExecutableCLSampler.dimension",
    "MIPStarRE.QPBT.ExecutableCLSampler.associatedMap",
    "MIPStarRE.QPBT.ExecutableCLSampler.downsize",
    "MIPStarRE.QPBT.ExecutableCLSampler.downsize_dimension",
    "MIPStarRE.QPBT.ExecutableCLSampler.downsize_associated",
    "MIPStarRE.QPBT.ExecutableCLSampler.sample_downsize",
    "MIPStarRE.QPBT.ExecutableCLSampler.downsize_time",
]
EXECUTABLE_CL_PRIVATE_STAGE_4A_SORRIES = [
    "MIPStarRE.QPBT.ExecutableCLSampler.downsizeCompiler_exists",
]
EXECUTABLE_CL_STAGE_4A_SORRIES = [
    *EXECUTABLE_CL_PRIVATE_STAGE_4A_SORRIES,
    "MIPStarRE.QPBT.ExecutableCLSampler.downsize_time",
]
EXECUTABLE_CL_IMPLEMENTATION_CONTRACT = {
    "writer_lane": "types",
    "owned_file": "MIPStarRE/QPBT/Game/Types.lean",
    "imports": [
        "Mathlib.Computability.TuringMachine.Computable",
        "Mathlib.Data.Nat.Log",
        "Mathlib.Probability.Distributions.Uniform",
        "MIPStarRE.QPBT.Basic.Field",
    ],
    "signature_manifest": {
        "path": "workflow/reviews/qpbt-059-f06a-pack-contract-a01.md",
        "begin_marker": "<!-- BEGIN F06A-QPBT059-SIGNATURES -->",
        "end_marker": "<!-- END F06A-QPBT059-SIGNATURES -->",
        "sha256": "368008b7b4ba84ff1dafe842acdb8af7005902a0fe9a376a8f7a690c86ba6b15",
    },
    "reused_api": [
        "Computability.Encoding",
        "Computability.encodeNat",
        "List.ofFn",
        "Finset.sup",
        "Nat.log",
        "StateTransition.EvalsToInTime",
        "Turing.FinTM2",
        "Turing.TM2OutputsInTime",
        "MIPStarRE.QPBT.CLSampler.downsize",
        "MIPStarRE.QPBT.CLSampler.sample_downsize",
        "MIPStarRE.QPBT.FieldData.coordinates",
        "MIPStarRE.QPBT.downsizeVector",
    ],
    "validation_commands": ["lake env lean MIPStarRE/QPBT/Game/Types.lean"],
    "allowed_minimal_sorries": EXECUTABLE_CL_STAGE_4A_SORRIES,
    "proof_complete_sorry_count": 0,
}
EXECUTABLE_CL_HISTORICAL_REPORT_PATH = Path(
    "workflow/reviews/qpbt-054-f06a-repair-a04.md"
)
EXECUTABLE_CL_HISTORICAL_REPORT_SHA256 = (
    "22db8cee76ff159412ced50941eb61d25bf94b7e4570147bd347d87cd0018ba7"
)
EXECUTABLE_CL_HISTORICAL_REPORT_HASH_ERROR = (
    "F06A-EXECUTABLE-CL: historical signature report hash mismatch"
)
EXECUTABLE_CL_SIGNATURE_REQUIRED_TERMS = (
    "(hn : 0 < n)",
    "abbrev CLPrefix",
    "abbrev CLFactorInput",
    "factor_cover : forall",
    "factor_disjoint : forall",
    "linear_supported : forall",
    "linear_depends : forall",
    "marginal_sum : forall",
    "| dimension",
    "| marginal",
    "| linear",
    "| factor",
    "def CLSamplerQuery.canonicalTapes",
    "def fieldExponentInput",
    "Turing.FinTM2",
    "Turing.TM2OutputsInTime",
    "execution.runInTime.toEvalsTo.steps",
    "structure FieldExponentProgram",
    "execution : forall n, 0 < n ->",
    "Computability.encodeNat (Q.exponent n)",
    "fieldProgram : FieldExponentProgram Q",
    "(S.validQueries n hn).sup (S.executedSteps n hn)",
    "Nat.max (S.queryTime n hn) (S.fieldProgram.steps n hn)",
    "(List.ofFn input).flatMap fun tape =>",
    "tape.flatMap (fun bit =>",
    "| false => [false, true]",
    "| true => [true, false]) ++ [false, false]",
    "Finset.univ",
    "s n * Q.exponent n",
    "s n * Nat.log 2 (Q.fieldSize n)",
    "RuntimeBigO S.downsize.time",
)
EXECUTABLE_CL_SIGNATURE_FORBIDDEN_PATTERNS = (
    r"\bin previous marginal range\b",
    r"\bin factor space for\b",
    r"\bvalidQueryFinset\b",
    r"\bfactor_(?:cover|disjoint)\s*:\s*Prop\b",
    r"\blinear_(?:supported|depends)\s*:\s*Prop\b",
    r"\bmarginal_sum\s*:\s*Prop\b",
    r"\boutput\s*:\s*SixTapeInput\s*->\s*List Bool\b",
    r"\bsteps\s*:\s*SixTapeInput\s*->\s*Nat\b",
    r"\brun\s*:\s*SixTapeInput\s*->\s*List Bool\s*->\s*Nat\s*->\s*Prop\b",
    r"\bdef\s+CLSamplerQuery\.tapes\b",
    r"\btime_eq_validQueryMax\b",
    r"Computability\.encodingNatBool\.encode\s*\(Encodable\.encode\s*\(List\.ofFn\s+input\)\)",
    r"\b(?:sorry|axiom|constant|opaque)\b",
)


def executable_cl_signature_errors(signature_block: str) -> list[str]:
    """Reject the concrete F06A contract defects found by QPBT-054."""
    errors = [
        f"executable CL signature omits required term: {term}"
        for term in EXECUTABLE_CL_SIGNATURE_REQUIRED_TERMS
        if term not in signature_block
    ]
    errors.extend(
        f"executable CL signature contains forbidden pattern: {pattern}"
        for pattern in EXECUTABLE_CL_SIGNATURE_FORBIDDEN_PATTERNS
        if re.search(pattern, signature_block, flags=re.IGNORECASE)
    )
    return errors


def executable_cl_historical_report_errors(repository_root: Path) -> list[str]:
    """Authenticate the full superseded F06A contract report bytes."""
    report_path = repository_root / EXECUTABLE_CL_HISTORICAL_REPORT_PATH
    if not report_path.is_file():
        return ["F06A-EXECUTABLE-CL: historical signature report file does not exist"]
    if hashlib.sha256(report_path.read_bytes()).hexdigest() != (
            EXECUTABLE_CL_HISTORICAL_REPORT_SHA256):
        return [EXECUTABLE_CL_HISTORICAL_REPORT_HASH_ERROR]
    return []


EXECUTABLE_CL_CONTRACT = {
    "statement": (
        "Define an admissible positive-index field family and its canonical "
        "source-coherent binary field-vector codec. Define a genuine six-input "
        "Turing sampler with distinct dimension, marginal, linear, and factor query "
        "modes with canonical blank normalization of unused tapes, data-valued "
        "chosen CL decompositions "
        "with dependent valid prefix and factor domains, its associated maps and "
        "exact sampler PMF, and an exact operational maximum TIME_S(n) over valid "
        "queries plus intrinsic exponent computation. "
        "Define executable downsizing and prove field size 2, dimension s(n) * "
        "log q(n), associated downsized maps, exact PMF pushforward, and the global "
        "positive-index RuntimeBigO compiler-cost bound."
    ),
    "encoding": (
        "For every positive n, q(n) = 2^(exponent n) with Odd (exponent n), and "
        "Nat.log 2 (q(n)) is the paper's log q(n). The canonical field codec is "
        "the F01-selected basis/table representation, with fixed coordinate order; "
        "no caller-supplied codec or coherence premise is accepted. SixTapeInput is "
        "Fin 6 -> List Bool. CLSamplerQuery has exactly four constructors and its "
        "positive-index proof supplies the canonical codec to every query. Its "
        "canonicalTapes encoding exposes the paper layouts and writes [] on every "
        "unused tape; it does not assert invariance under arbitrary unused-tape "
        "contents. "
        "stage.val encodes paper j = stage.val + 1. packSixTapes first fixes tape "
        "order with List.ofFn, expands false as 01 and true as 10, and appends the "
        "00 terminator after each of the six tapes. It is an injective, linear, "
        "self-delimiting encoding of exact length 2 * (sum tape lengths + 6). "
        "CLQueryDecomposition carries selected "
        "marginals, prefix-range-indexed factors, factor-space linear maps, and the "
        "lem:cl-kth realization equations, partition, support, and dependency laws as "
        "data. CLPrefix and CLFactorInput are the dependent valid u/y subtypes; "
        "malformed encodings and index zero are outside the paper contract. An "
        "intrinsic FieldExponentProgram computes exponent n from n; it is attached to "
        "the executable sampler and is not a fifth sampler query mode. "
        "The sampler PMF is exactly CLSampler.sample from one shared uniform seed."
    ),
    "boundary_hypotheses": (
        "The executable sampler is supplied as the source-defined machine together with "
        "intrinsic semantic correctness data; no theorem asserts that every mathematical "
        "CLSampler has an executable realization. Its associated maps and decomposition "
        "choices are data-valued and include the exact F06 lem:cl-kth laws. The machine "
        "has six logical input tapes with canonical blank normalization; the boundary "
        "does not claim the paper's stronger arbitrary unused-payload invariance. Its "
        "execution field contains a genuine TM2OutputsInTime witness and its exact "
        "step count is runInTime.toEvalsTo.steps. The FinTM2 input packing is exactly "
        "the paper's linear dual-rail, 00-terminated representation and preserves the "
        "six logical tape boundaries. "
        "Every paper-labelled pointwise claim carries 0 < n, and downsizing carries "
        "1 <= level. The paper does not specify how downsize computes log q(n); the "
        "faithful executable boundary therefore attaches a concrete FieldExponentProgram "
        "to the sampler rather than fabricating one from an arbitrary exponent family. "
        "TIME_S(n) is the exact maximum of that field-exponent execution and the "
        "valid-query finite maximum "
        "over Finset.univ; time is a definition, not an arbitrary upper-bound field. "
        "RuntimeBigO is global over positive indices. The source's omitted linear u/y "
        "quantifiers and the prefix/downsize index typos are preserved as explicit "
        "paper-gap notes A02-004/A02-006 and repaired only at the dependent Lean "
        "boundary. F01's source-coherent codec construction and table algorithm remain "
        "the tracked G16/K03A proof obligation, never a public codec-correctness input. "
        "The compiler-cost proof must account for parsing, prefix inversion, simulation, "
        "and ordered log-q factor-block output; it may not use a generic obligation. "
        "F06A alone owns def:sampler, def:sampler-sample, def:downsize_sampler, and "
        "lem:downsize_sampler. F06 owns only conditionally-linear.tex:1-552; "
        "F07A-DETYPING, QPBT-043, K03, and K04 own none of the generic executable "
        "sampler, query, distribution, downsize, dimension, or runtime clauses. No "
        "generic Hypotheses, Assumptions, bridge, residual, repair, witness, package, "
        "producer, arbitrary implication input, or fabricated Turing theorem is permitted."
    ),
    "paper_assumptions": (
        "Positive integers n with an admissible field size function q(n), a dimension "
        "function s(n), one ell-level six-input Turing sampler whose four query modes "
        "return chosen marginal maps, linear maps, and factor indicators for associated "
        "Alice/Bob CL functions, and ell >= 1 for executable downsizing."
    ),
    "lean_assumptions": (
        "An exponent family with Odd (exponent n) guarded by 0 < n, the canonical F01 "
        "source-coherent coordinate codec, an explicit Fin 6 binary query boundary "
        "with canonical blanks on unused tapes, the paper's injective linear dual-rail "
        "packing with one 00 terminator per tape, data-valued nonunique "
        "CLQueryDecomposition records whose "
        "CLPrefix/CLFactorInput domains satisfy the F06 laws, an operational six-input "
        "machine, a concrete intrinsic FieldExponentProgram, genuine TM2OutputsInTime "
        "witnesses for both the four source queries and exponent computation, exact "
        "extracted execution steps, "
        "and a constructed operational maximum charging both kinds of execution; no "
        "executable-realization, codec-coherence, runtime, bridge, or arbitrary "
        "obligation premise is added to a paper theorem."
    ),
    "paper_conclusion": (
        "The sampler has associated CL maps, chosen decompositions, exact distribution, "
        "and TIME_S(n); its executable downsize has field size 2, dimension s(n) log "
        "q(n), associated downsized CL maps, exact sampler-law pushforward, and global "
        "positive-index runtime O(TIME_S(n) log q(n))."
    ),
    "lean_conclusion": (
        "The exact four encoded query results compute through six-tape operational run "
        "witnesses on canonical blank-normalized tapes and dependent valid-query "
        "domains; no arbitrary unused-payload invariance is claimed. Associated, "
        "sample, queryTime_eq_validQueryMax, and time_eq_max are callable; time_eq_max "
        "charges the intrinsic exponent program needed by downsize. Downsize has the canonical "
        "binary codec, an internal s(n)*exponent(n) representation width proved equal "
        "to dimension s(n)*Nat.log 2(Q.fieldSize n), exact pointwise map "
        "correspondence for every 0 < n, exact PMF.map pushforward from one shared "
        "sampler law, and a proved global-positive RuntimeBigO compiler-cost theorem "
        "under 1 <= level. The packed six-tape input is self-delimiting and has exact "
        "length 2 * (sum tape lengths + 6). The G16/K03A representation-coherence obligation remains "
        "tracked and is not exposed as a public input."
    ),
    "verdict": "faithful boundary",
}
TYPED_PREREQUISITES = [EXECUTABLE_CL_OWNER_ID]
F07_FINITENESS_CONTRACT = {
    "statement": (
        "Define finite type and edge support and its graph-distribution semantics. "
        "Define a typed sampler on the constant FieldVector question-content carrier. "
        "Define heterogeneous typed questions and answers and total dependent deciders "
        "over arbitrary fibers. Define mathematical typed-sampler downsizing and its PMF "
        "theorem. Among question/answer content fibers, only the sampler carrier is "
        "asserted finite."
    ),
    "encoding": (
        "TypeGraph stores a nonempty symmetric Finset of ordered endpoints: a loop occurs "
        "once and each non-loop occurs in both orientations. Its uniform PMF therefore "
        "has the paper denominator 2m-k. Typed questions use Sigma fibers, and "
        "TypedDecider is total over every type pair without erasing question or answer "
        "fibers. TypedSampler.downsize retains the graph and level, downsizes both CL "
        "families pointwise, and sample_downsize is the exact PMF pushforward."
    ),
    "boundary_hypotheses": (
        "The type index and ordered-edge support are finite. Finiteness is asserted only "
        "for the constant FieldVector question-content carrier used by TypedSampler. "
        "TypedQuestion and TypedDecider admit arbitrary dependent question and answer "
        "fibers without pointwise finiteness assumptions. G02 alone supplies the pointwise "
        "finite question and answer families required by the mathematical game consumer. "
        "F06A-EXECUTABLE-CL is the sole generic six-input sampler/query/downsize machine "
        "base. The mathematical typed downsizing callables here do not claim the typed "
        "Turing representation or runtime equation. Typed verifier/game, executable "
        "typed interfaces, graph simulation, detyping, and typed/detyping cost clauses "
        "are owned by F07A-DETYPING and frozen by QPBT-043; F07A, K03, and K04 own none "
        "of F06A's generic clauses."
    ),
    "paper_assumptions": (
        "A finite type set, an undirected graph that may contain self-loops, typed CL "
        "families over the generic executable sampler, executable typed sampler/decider "
        "data, and a selected field basis for downsizing."
    ),
    "lean_assumptions": (
        "F06A's exact generic executable base; a nonempty symmetric finite ordered-edge "
        "support and certified maps on the constant FieldVector carrier; FieldData only "
        "for downsizing; generic sigma/dependent question, answer, and decider fibers "
        "carry no pointwise finiteness assumption."
    ),
    "lean_conclusion": (
        "A uniform ordered-edge PMF preserving loop/orientation weight, its callable type "
        "marginal, a graph-preserving pointwise downsizing operation with exact PMF "
        "pushforward, and a total dependent decider over arbitrary fibers. Generic "
        "executable behavior is inherited only from F06A; typed executable representation "
        "and costs remain explicit F07A-DETYPING/QPBT-043 obligations."
    ),
}
DETYPING_OWNER_ID = "F07A-DETYPING"
DETYPING_SOURCE_ANCHORS = [
    {
        "path": "references/2001.04383v3/sections/dependencies/types.tex",
        "label": "lem:detyping-verifiers",
        "generated_lines": [197, 579],
        "original_lines": [3763, 4145],
    },
    {
        "path": "references/2001.04383v3/sections/dependencies/types.tex",
        "label": "def:typed-sampler",
        "generated_lines": [95, 195],
        "original_lines": [3661, 3761],
    },
    {
        "path": "references/2001.04383v3/sections/top-level/preliminaries.tex",
        "label": "",
        "generated_lines": [19, 32],
        "original_lines": [916, 929],
    },
    {
        "path": "references/2001.04383v3/sections/top-level/preliminaries.tex",
        "label": "thm:universal-tm",
        "generated_lines": [77, 137],
        "original_lines": [974, 1034],
    },
    {
        "path": "references/2001.04383v3/sections/top-level/preliminaries.tex",
        "label": "",
        "generated_lines": [171, 200],
        "original_lines": [1068, 1097],
    },
    {
        "path": "references/2001.04383v3/sections/top-level/nonlocal-games.tex",
        "label": "def:decider",
        "generated_lines": [612, 678],
        "original_lines": [3489, 3555],
    },
]
DETYPING_SOURCE_ANCHOR = DETYPING_SOURCE_ANCHORS[0]
DETYPING_SOURCE_RANGE = DETYPING_SOURCE_ANCHOR["generated_lines"]
DETYPING_PREREQUISITES = [GAME_SEMANTICS_OWNER_ID, "F07-TYPED"]
DETYPING_GAP_IDS = ["G24", "G25", "G26"]
DETYPING_LEAN_NAMES = [
    "MIPStarRE.QPBT.TypedNormalFormVerifier",
    "MIPStarRE.QPBT.TypedNormalFormVerifier.game",
    "MIPStarRE.QPBT.TypeGraph.neighborIndicator",
    "MIPStarRE.QPBT.TypeGraph.vertexEncoding",
    "MIPStarRE.QPBT.TypeGraph.graphSampler",
    "MIPStarRE.QPBT.TypeGraph.graphEvent",
    "MIPStarRE.QPBT.TypeGraph.graphEvent_probability",
    "MIPStarRE.QPBT.TypeGraph.graphEvent_conditioned_types",
    "MIPStarRE.QPBT.detypeCL",
    "MIPStarRE.QPBT.TypedSampler.detype",
    "MIPStarRE.QPBT.TypedDecider.detype",
    "MIPStarRE.QPBT.TypedNormalFormVerifier.detype",
    "MIPStarRE.QPBT.detyping_complete",
    "MIPStarRE.QPBT.detyping_sound",
    "MIPStarRE.QPBT.detyping_entanglement",
    "MIPStarRE.QPBT.detyping_level",
    "MIPStarRE.QPBT.detyping_dimension",
    "MIPStarRE.QPBT.detyping_sampler_time",
    "MIPStarRE.QPBT.detyping_decider_time",
    "MIPStarRE.QPBT.detyping_descriptions_time",
]
DETYPING_INTEGRITY_SHA256 = (
    "e92060525909f5c895bbbf24c21fb1ff0edc41fe2333eec8176cb902ae50543e"
)
DETYPING_NODE_CONTRACT_SHA256 = (
    "b27b4ca90be6460984ea51c60332115fa3031b99999573efbb5410319b2e4706"
)
DETYPING_GAP_CONTRACT_SHA256 = {
    "G24": "21b5f8f9b5e64c2b982f622c67dd3bf202508ce4b251c36c9d1812323eea5ca1",
    "G25": "3072138996662d5cd4d737e3753af902461d529c38dd372d70f3c0a8520e5517",
    "G26": "07cdf7c1e5c45414374d16f30b04c4870ee5a659ea2f4600f7fa0a2a673dca1d",
}
DETYPING_AUTHENTICATED_MARKDOWN = {
    Path("docs/paper-gaps/detyping-executable-boundaries.md"):
        "c825816b8b696833fd55935105468ce4e590abae51269b36f6c6854a878905df",
}
MAGIC_GAME_OWNER_ID = "F08-MAGIC-GAME"
MAGIC_GAME_PREREQUISITES = [
    "F03-MEASUREMENT", GAME_SEMANTICS_OWNER_ID, "F07-TYPED",
]
CLASSICAL_LDT_GAME_CORE_ID = "F09A-LDT-GAME-CORE"
CLASSICAL_LDT_ANALYSIS_ID = "F09-LDT-GAME"
QPBT_GAME_ID = "G02-GAME"
CLASSICAL_LDT_GAP_IDS = ["G22", "G23"]
CLASSICAL_LDT_GAME_CORE_SOURCE_ANCHORS = [
    {
        "path": "references/2001.04383v3/sections/dependencies/classical-ldt.tex",
        "label": "def:line",
        "generated_lines": [88, 258],
        "original_lines": [4250, 4420],
    },
    {
        "path": "references/2001.04383v3/sections/dependencies/classical-ldt.tex",
        "label": "def:line-point-dist",
        "generated_lines": [262, 273],
        "original_lines": [4424, 4435],
    },
    {
        "path": "references/2001.04383v3/sections/dependencies/classical-ldt.tex",
        "label": "fig:ld-decider",
        "generated_lines": [306, 377],
        "original_lines": [4468, 4539],
    },
    {
        "path": "references/2001.04383v3/sections/qpbt/qpbt-game-and-soundness.tex",
        "label": "",
        "generated_lines": [235, 238],
        "original_lines": [5281, 5284],
    },
    {
        "path": "references/2001.04383v3/sections/qpbt/qpbt-game-and-soundness.tex",
        "label": "",
        "generated_lines": [248, 254],
        "original_lines": [5294, 5300],
    },
    {
        "path": "references/2001.04383v3/sections/qpbt/qpbt-game-and-soundness.tex",
        "label": "",
        "generated_lines": [271, 289],
        "original_lines": [5317, 5335],
    },
    {
        "path": "references/2001.04383v3/sections/top-level/preliminaries.tex",
        "label": "def:canonical-complement",
        "generated_lines": [306, 383],
        "original_lines": [1203, 1280],
    },
    {
        "path": "references/2001.04383v3/sections/dependencies/finite-fields.tex",
        "label": "",
        "generated_lines": [250, 263],
        "original_lines": [1566, 1579],
    },
]
CLASSICAL_LDT_GAME_CORE_SOURCE_SHA256 = {
    "references/2001.04383v3/sections/dependencies/classical-ldt.tex":
        "2314b141dbe31a12718244fabbf15a96f630351b7e22ded0fd21edf294039638",
    "references/2001.04383v3/sections/qpbt/qpbt-game-and-soundness.tex":
        "30c735197503d81b37dc33129f15270fe216cc9458d96620a6488109994e62ea",
    "references/2001.04383v3/sections/top-level/preliminaries.tex":
        "045ef86cf9bb1ca5898f66de29f814fc869a54d357160286322c4cad7786aab1",
    "references/2001.04383v3/sections/dependencies/finite-fields.tex":
        "379d970ae1b67412db5d25233856702f4ca69e8ee2d11b0afcf7c767b767b9cd",
}
CLASSICAL_LDT_GAME_CORE_AUTHENTICATED_SOURCES = [
    {
        "path": path,
        "sha256": digest,
        "anchors": [anchor for anchor in CLASSICAL_LDT_GAME_CORE_SOURCE_ANCHORS
                    if anchor["path"] == path],
    }
    for path, digest in CLASSICAL_LDT_GAME_CORE_SOURCE_SHA256.items()
]
CLASSICAL_LDT_SOURCE_MANIFEST_MARKERS = (
    "<!-- BEGIN F09A-SOURCE-MANIFEST -->",
    "<!-- END F09A-SOURCE-MANIFEST -->",
)
CLASSICAL_LDT_LOCAL_INSTANCE_NAMES = [
    "classicalLDTGaloisFieldFintype",
    "classicalLDTGaloisFieldDecidableEq",
]
CLASSICAL_LDT_COMBINED_IMPORT_PROBE = {
    "pauli_first": [
        "MIPStarRE.QPBT.Basic.Pauli",
        "MIPStarRE.QPBT.Basic.Polynomial",
        "MIPStarRE.QPBT.Game.Types",
        "MIPStarRE.QPBT.Game.Parameters",
        "MIPStarRE.QPBT.Game.MagicSquare.Defs",
        "MIPStarRE.QPBT.Game.ClassicalLDT",
    ],
    "classical_ldt_first": [
        "MIPStarRE.QPBT.Game.ClassicalLDT",
        "MIPStarRE.QPBT.Game.MagicSquare.Defs",
        "MIPStarRE.QPBT.Game.Parameters",
        "MIPStarRE.QPBT.Game.Types",
        "MIPStarRE.QPBT.Basic.Polynomial",
        "MIPStarRE.QPBT.Basic.Pauli",
    ],
}
CLASSICAL_LDT_COMBINED_IMPORT_PROBE_MARKERS = (
    "<!-- BEGIN F09A-COMBINED-IMPORT-PROBE -->",
    "<!-- END F09A-COMBINED-IMPORT-PROBE -->",
)
CLASSICAL_LDT_GAME_CORE_PREREQUISITES = ["F01-FIELD", "F02-CODE", "F06-CL"]
CLASSICAL_LDT_GAME_CORE_LEAN_NAMES = [
    "MIPStarRE.QPBT.ClassicalLDTSeed",
    "MIPStarRE.QPBT.classicalLDTSeedEquiv",
    "MIPStarRE.QPBT.standardDirection",
    "MIPStarRE.QPBT.truncateDirection",
    "MIPStarRE.QPBT.firstNonzeroCoordinate",
    "MIPStarRE.QPBT.fieldElementIndex",
    "MIPStarRE.QPBT.chi",
    "MIPStarRE.QPBT.canonicalLineProjection",
    "MIPStarRE.QPBT.AffineLine",
    "MIPStarRE.QPBT.AffineLine.pointAt",
    "MIPStarRE.QPBT.AffineLine.parameter?",
    "MIPStarRE.QPBT.AxisLineQuestion",
    "MIPStarRE.QPBT.DiagonalLineQuestion",
    "MIPStarRE.QPBT.AxisLineQuestion.line",
    "MIPStarRE.QPBT.DiagonalLineQuestion.line",
    "MIPStarRE.QPBT.pointCLMap",
    "MIPStarRE.QPBT.axisLineCLMap",
    "MIPStarRE.QPBT.diagonalLineCLMap",
    "MIPStarRE.QPBT.axisLinePointDistribution",
    "MIPStarRE.QPBT.diagonalLinePointDistribution",
    "MIPStarRE.QPBT.BoundedUnivariatePolynomial",
    "MIPStarRE.QPBT.BoundedUnivariatePolynomial.eval",
    "MIPStarRE.QPBT.IndividualLDTQuestion",
    "MIPStarRE.QPBT.IndividualLDTAnswer",
    "MIPStarRE.QPBT.simultaneousIndividualLDTOne",
    "MIPStarRE.QPBT.fieldElementIndex_apply",
    "MIPStarRE.QPBT.fieldElementIndex_testBit",
    "MIPStarRE.QPBT.chi_val",
    "MIPStarRE.QPBT.chi_fiber_card",
    "MIPStarRE.QPBT.chi_map_uniform",
    "MIPStarRE.QPBT.truncateDirection_apply_of_lt",
    "MIPStarRE.QPBT.truncateDirection_apply_of_le",
    "MIPStarRE.QPBT.truncateDirection_idempotent",
    "MIPStarRE.QPBT.canonicalLineProjection_zero",
    "MIPStarRE.QPBT.canonicalLineProjection_apply_of_ne_zero",
    "MIPStarRE.QPBT.canonicalLineProjection_direction_of_ne_zero",
    "MIPStarRE.QPBT.canonicalLineProjection_idempotent",
    "MIPStarRE.QPBT.canonicalLineProjection_sub_mem_span",
    "MIPStarRE.QPBT.canonicalLineProjection_add_smul",
    "MIPStarRE.QPBT.AffineLine.parameter?_sound",
    "MIPStarRE.QPBT.AffineLine.parameter?_isSome_iff",
    "MIPStarRE.QPBT.AffineLine.parameter?_unique_of_ne_zero",
    "MIPStarRE.QPBT.AffineLine.parameter?_zero_direction",
    "MIPStarRE.QPBT.pointCLMap_apply",
    "MIPStarRE.QPBT.axisLineCLMap_apply",
    "MIPStarRE.QPBT.diagonalLineCLMap_apply",
    "MIPStarRE.QPBT.axisLinePointDistribution_eq_map",
    "MIPStarRE.QPBT.diagonalLinePointDistribution_eq_map",
    "MIPStarRE.QPBT.axisLinePointDistribution_incident",
    "MIPStarRE.QPBT.diagonalLinePointDistribution_incident",
    "MIPStarRE.QPBT.axisLine_selector_uniform",
    "MIPStarRE.QPBT.diagonalLine_prefix_agrees",
    "MIPStarRE.QPBT.BoundedUnivariatePolynomial.eval_zero",
    "MIPStarRE.QPBT.BoundedUnivariatePolynomial.eval_congr",
    "MIPStarRE.QPBT.simultaneousIndividualLDTOne_point_point",
    "MIPStarRE.QPBT.simultaneousIndividualLDTOne_axisLine_axisLine",
    "MIPStarRE.QPBT.simultaneousIndividualLDTOne_diagonalLine_diagonalLine",
    "MIPStarRE.QPBT.simultaneousIndividualLDTOne_axisLine_point",
    "MIPStarRE.QPBT.simultaneousIndividualLDTOne_point_axisLine",
    "MIPStarRE.QPBT.simultaneousIndividualLDTOne_diagonalLine_point",
    "MIPStarRE.QPBT.simultaneousIndividualLDTOne_point_diagonalLine",
    "MIPStarRE.QPBT.simultaneousIndividualLDTOne_nonincident",
    "MIPStarRE.QPBT.simultaneousIndividualLDTOne_unlisted",
    "MIPStarRE.QPBT.simultaneousIndividualLDTOne_zero_direction",
]
CLASSICAL_LDT_GAME_CORE_LAW_NAMES = CLASSICAL_LDT_GAME_CORE_LEAN_NAMES[25:]
CLASSICAL_LDT_GAME_CORE_F06_REUSED_API = [
    "MIPStarRE.QPBT.FieldVector",
    "MIPStarRE.QPBT.ConditionallyLinearMap",
    "MIPStarRE.QPBT.CLSampler.sample",
]
CLASSICAL_LDT_FORBIDDEN_ANCESTORS = {
    "F06A-EXECUTABLE-CL", "F07-TYPED", "F07A-DETYPING",
}
CLASSICAL_LDT_GAME_CORE_SIGNATURE_REQUIRED_TERMS = (
    "noncomputable local instance classicalLDTGaloisFieldFintype (k : Nat)",
    "Fintype.ofFinite (GaloisField 2 k)",
    "noncomputable local instance classicalLDTGaloisFieldDecidableEq (k : Nat)",
    "Classical.decEq (GaloisField 2 k)",
    "deriving DecidableEq, Fintype",
    "| .point _ => GaloisField 2 k",
    "| .axisLine _ => BoundedUnivariatePolynomial k d",
    "| .diagonalLine _ => BoundedUnivariatePolynomial k (m * d)",
    "Nat.testBit (fieldElementIndex D s).val i.val",
    "decide (D.coordinates s i = 1)",
    "Fintype.card {s : GaloisField 2 k // chi D hm s = i}",
    "chi D hm pair.1.selector) i = (m : ENNReal)⁻¹",
    "(hpair : axisLinePointDistribution D hm pair ≠ 0)",
    "(hpair : diagonalLinePointDistribution D hm pair ≠ 0)",
    "(hfg : ∀ i, f i = g i)",
    "| some t => decide (f.eval t = a)",
    "| none => false",
    "(hq : (q.line D hm).direction = 0)",
    "if u = (q.line D hm).base then decide (f.eval 0 = a) else false",
)
CLASSICAL_LDT_GAME_CORE_SIGNATURE_FORBIDDEN_PATTERNS = (
    r"\b(?:sorry|admit|axiom|constant|opaque)\b",
    r"\b(?:Hypotheses|Assumptions|Obligations|bridge|residual|repair|witness|package|producer)\b",
    r"\b(?:AdmissibleFieldFamily|ExecutableCLSampler|TypeGraph|TypedQuestion|TypedSampler|TypedDecider)\b",
    r"MIPStarRE\.QPBT\.Analysis\.",
)
CLASSICAL_LDT_GAME_CORE_DECLARATION_SHA256 = {
    "MIPStarRE.QPBT.ClassicalLDTSeed": "77b4f5ca2711e5675391b15ea2f952158e7bcc4bda2dd24bfba6fbf30e03403a",
    "MIPStarRE.QPBT.classicalLDTSeedEquiv": "9807dd9040729ad0259febbeeea87e5cf849c27b9ef77e6fd05b048fdac981c7",
    "MIPStarRE.QPBT.standardDirection": "c069c03f31c26e2399c1669287cc6ad5d1896a8a15e54f4e1513042ecea54873",
    "MIPStarRE.QPBT.truncateDirection": "32d98921f50478e26fbc0db3f0e05a98c3738e74c11afd1bdde7e58647721af8",
    "MIPStarRE.QPBT.firstNonzeroCoordinate": "66de6ee5823296c489e354626d954233e467108257b0ac793686557b6af808e8",
    "MIPStarRE.QPBT.fieldElementIndex": "27e6c5d568a54302f4311b3cc81c383841f1bcbb7903d776c8c8ccccd0f4854d",
    "MIPStarRE.QPBT.chi": "fbf8de7ba86ba1e3a2166271fb838b3f3db8a743d28ed5e59fd40cf7a9f443fd",
    "MIPStarRE.QPBT.canonicalLineProjection": "90e6ec559d047971a263a3e676da5900906deb81471df31a19b6f82998a175e6",
    "MIPStarRE.QPBT.AffineLine": "e0084924fe34fbb141858398f43a818c3261c9b3668176651b49e49704a5b9c7",
    "MIPStarRE.QPBT.AffineLine.pointAt": "463a0bfc551135637024757bbea8fb84d17f889aa17b365b74faec885a2b16cd",
    "MIPStarRE.QPBT.AffineLine.parameter?": "385bf20abf42bef280340e0f5a81238dbfd560ae83ea4d399befc942d3086610",
    "MIPStarRE.QPBT.AxisLineQuestion": "0b556894429810836bdbed5e4f62044275ebb56df7a37da73e9ef699488e8706",
    "MIPStarRE.QPBT.DiagonalLineQuestion": "bb0fccda37bd029707fcbcb32c7e6e40d871232f1ca85e3bbdf8b61d30572efe",
    "MIPStarRE.QPBT.AxisLineQuestion.line": "4791434da045625b021b9e7a809a392ca7bd3547ae02695c9b9229edc8afb47c",
    "MIPStarRE.QPBT.DiagonalLineQuestion.line": "ae96c372ea2013c068226aecff16ecc94b66cfadad59c9fb753168244f85a90c",
    "MIPStarRE.QPBT.pointCLMap": "a9a03ce2c4a34107544681f2908eb2caeec44a7793b8b31a693ee9f4015cf8ea",
    "MIPStarRE.QPBT.axisLineCLMap": "5a5cf63a20518d7e608cad6cdbec10aeb63b4aa056b1243eef4a69486796830e",
    "MIPStarRE.QPBT.diagonalLineCLMap": "35249cd6543d9d47e56c51466381a5b47db1416c9c86210972ae2ee8750d4611",
    "MIPStarRE.QPBT.axisLinePointDistribution": "c143aa6bcc896d25e9eccc924f28d227b0f802bdfc4b4e479de65c87a189cd97",
    "MIPStarRE.QPBT.diagonalLinePointDistribution": "a04003e9384d0bfe54a43b0c0a1b9f465f3190ce5816a5865f7ed311c71471fd",
    "MIPStarRE.QPBT.BoundedUnivariatePolynomial": "3adfcef52de9a3a4ed3101ba8f7ce3bd813e1e4d60d52d6d793ebcf0aa049cfd",
    "MIPStarRE.QPBT.BoundedUnivariatePolynomial.eval": "37a51c504a642162f10404aacb49183dbe65dc24a4adcf74cf19178fc54eb904",
    "MIPStarRE.QPBT.IndividualLDTQuestion": "1567475e627b77922cda21cf5fb94ed54086e4fc8f50e8f83636f47a659f1bcf",
    "MIPStarRE.QPBT.IndividualLDTAnswer": "5b288e95859709a511031403092749ca1b8d4c5547400cf9cf536beb532147e8",
    "MIPStarRE.QPBT.simultaneousIndividualLDTOne": "116ae9adb5f7a1f8c8bb78b8d535ff82197137f9ebca696b0fca52de06f5a8ed",
    "MIPStarRE.QPBT.fieldElementIndex_apply": "50973c55a852f1095a3b6fa981a09c9080205f463e46510a1aaa85762492b662",
    "MIPStarRE.QPBT.fieldElementIndex_testBit": "57a9a6b71641ce0d6190c5d346b4d5c85c977e5e2206543c7d14818b4aca9c72",
    "MIPStarRE.QPBT.chi_val": "24c89b3cfb91d8180d49a92d950ebded497e5e674b144ccbbb7e095fff06e487",
    "MIPStarRE.QPBT.chi_fiber_card": "ca1e80179f0a588a6a582bacaa50526ff3ff908b26dd993a6afa19097786ee53",
    "MIPStarRE.QPBT.chi_map_uniform": "798f88400391b5e24380105c76b32d2d5f53e76fcd5b8a140702e25f2bfb187d",
    "MIPStarRE.QPBT.truncateDirection_apply_of_lt": "5e8c21c2c490e7fda4fb0f9e52d9a65149458be9361c2008418505ceeae02adf",
    "MIPStarRE.QPBT.truncateDirection_apply_of_le": "3c93e202597c63fd1cdfbf73602e0acd2c40a3650e6054899e1c24cbbf624611",
    "MIPStarRE.QPBT.truncateDirection_idempotent": "a0709dbd9df757c1c0ba63ffd847606f1b075990e14645cb93c30b4c92701dd7",
    "MIPStarRE.QPBT.canonicalLineProjection_zero": "6cad9c993dc7bc0d6422af489453bb20f1083e2fa5f4db33e5602f7c3d82d419",
    "MIPStarRE.QPBT.canonicalLineProjection_apply_of_ne_zero": "f4911ec5415360b9485880adb41bbeb7878201a37a2505923b79352287606fb6",
    "MIPStarRE.QPBT.canonicalLineProjection_direction_of_ne_zero": "c3acdcdd2b2705ba178f7a13d7c452af45a0ef7461e12246aa4812aafdd32f8f",
    "MIPStarRE.QPBT.canonicalLineProjection_idempotent": "afdf154260a7ae2b1488b445523b7d94baa7f130e378b044785d85b9fec9f516",
    "MIPStarRE.QPBT.canonicalLineProjection_sub_mem_span": "8996271e6c5d77abbd85060e3f7d317937fd56085e2108a7f51ef2cbca614f05",
    "MIPStarRE.QPBT.canonicalLineProjection_add_smul": "e691e6648e48e558fcb0732c319205954bbc40150e65e4c4161215121b995515",
    "MIPStarRE.QPBT.AffineLine.parameter?_sound": "f92b43a8a41150f577c4645c87f3c29cf2440a968fc792dc9abea7a4562038f4",
    "MIPStarRE.QPBT.AffineLine.parameter?_isSome_iff": "8d2cf41f5d2afbe255bff97e0f5ca4022072bf514c631ce4c44702c5f38e5d47",
    "MIPStarRE.QPBT.AffineLine.parameter?_unique_of_ne_zero": "88ede259d5bb60b71e6e4f19f6c5d316a62451b5b4aae34ecd4cfa243a7105c6",
    "MIPStarRE.QPBT.AffineLine.parameter?_zero_direction": "c768f445f0a088f7d45125816804f2c7cf3bfedbeeab861ac5911794aba27bab",
    "MIPStarRE.QPBT.pointCLMap_apply": "c08a882c7c25faa1c0883efccff81ca3c6e6c84212a73e16ac12a51b964fe12e",
    "MIPStarRE.QPBT.axisLineCLMap_apply": "0138f9576389c3b1e1cfdbd39165035e2c7985a1c902674d78dc6a97b91fa483",
    "MIPStarRE.QPBT.diagonalLineCLMap_apply": "85f0b958d52cfd41a922724796e73e55bb2dd4ac2c18df7cc7dc7efdd945564f",
    "MIPStarRE.QPBT.axisLinePointDistribution_eq_map": "3da01e7043eb16ea3b7d2d8fe963bd49456086ce4492cb587c4671c652d6c5d5",
    "MIPStarRE.QPBT.diagonalLinePointDistribution_eq_map": "8cfb5728e5dab7948e397209d5d7800a2c258c4ecca571b0c948279f31ae48d1",
    "MIPStarRE.QPBT.axisLinePointDistribution_incident": "3cfcc085503249f49e301976479e33bf38ccb0a987debb5567d7446bb3fa1634",
    "MIPStarRE.QPBT.diagonalLinePointDistribution_incident": "d1efddb70634688fb51aa1402b9eed37242edd98bb9c1c8b11c83c097868c958",
    "MIPStarRE.QPBT.axisLine_selector_uniform": "c9a90b7a073f7388898715b19af3501c8cd41484eb33ad11685e00942cf70ea3",
    "MIPStarRE.QPBT.diagonalLine_prefix_agrees": "8c9089416d0319defa345c08c64ddd1d73d039174f22049dbfa67407635c212b",
    "MIPStarRE.QPBT.BoundedUnivariatePolynomial.eval_zero": "9a74fd534dbcacd5c6fd41f22a3243d74b5f7d1516350e6cfec08cdd8bff1ac2",
    "MIPStarRE.QPBT.BoundedUnivariatePolynomial.eval_congr": "21260cd34b8b1dd855ae48d609bd3213e39b50baad95e4c6cd6a764378a0504f",
    "MIPStarRE.QPBT.simultaneousIndividualLDTOne_point_point": "bd6c935a353bbfbf9bae3a013d7693b92ccb3e39ab3689bef71dabe30b085a4b",
    "MIPStarRE.QPBT.simultaneousIndividualLDTOne_axisLine_axisLine": "53c0af4de97311c119de3df4c8c6df94d1a44fbca756d26e388a09b12c32c12e",
    "MIPStarRE.QPBT.simultaneousIndividualLDTOne_diagonalLine_diagonalLine": "d96b3bce91736b874850d67c1d78ffb43d3fd1b231600e7bc57278ae4fc1705e",
    "MIPStarRE.QPBT.simultaneousIndividualLDTOne_axisLine_point": "ea76375fac2a74c9b0d466fbc17a55b3a74a9c66ce8d29fc8d4e34a09bb9b5b2",
    "MIPStarRE.QPBT.simultaneousIndividualLDTOne_point_axisLine": "48581f2773dd14420b44b0cc3d8d2f93f8b31737af1ccb79eab9d60264cc30d5",
    "MIPStarRE.QPBT.simultaneousIndividualLDTOne_diagonalLine_point": "a039052139320f30304436fc6acbd57ebfbb32ff4f84feb3050f7ab97117dac1",
    "MIPStarRE.QPBT.simultaneousIndividualLDTOne_point_diagonalLine": "e8a9494a237eb68d5c46c8787e0684f3c7400eccfa6a13803152ffa18e2d7233",
    "MIPStarRE.QPBT.simultaneousIndividualLDTOne_nonincident": "b60350ad3e2c6f6566d0320eea07acb5f24560732aa91e5ec0d0b797339d19aa",
    "MIPStarRE.QPBT.simultaneousIndividualLDTOne_unlisted": "c01e6d5efc9fc9f8760e00c1ccf8749bca06382c17601d216fbc8706341bb0d9",
    "MIPStarRE.QPBT.simultaneousIndividualLDTOne_zero_direction": "01a5359710666659e0da8051551d6cc322db8c7cfaf98cc603d79bd5a23c2bf6",
}


def _strip_lean_comments(text: str) -> str:
    """Remove line and nested block comments while preserving line structure."""
    result: list[str] = []
    index = 0
    block_depth = 0
    while index < len(text):
        if block_depth:
            if text.startswith("/-", index):
                block_depth += 1
                result.extend("  ")
                index += 2
            elif text.startswith("-/", index):
                block_depth -= 1
                result.extend("  ")
                index += 2
            else:
                result.append("\n" if text[index] == "\n" else " ")
                index += 1
        elif text.startswith("--", index):
            while index < len(text) and text[index] != "\n":
                result.append(" ")
                index += 1
        elif text.startswith("/-", index):
            block_depth = 1
            result.extend("  ")
            index += 2
        else:
            result.append(text[index])
            index += 1
    return "".join(result)


def classical_ldt_declaration_segments(
        signature_block: str) -> tuple[list[str], dict[str, str], list[str]]:
    """Extract ordered public declarations from the signed F09A Lean block."""
    errors: list[str] = []
    if (signature_block.count("```lean") != 1 or
            signature_block.count("```") != 2 or
            not signature_block.startswith("```lean\n") or
            not signature_block.endswith("\n```")):
        return [], {}, ["classical LDT signature must contain one exact Lean fence"]
    code = signature_block[len("```lean\n"):-len("\n```")]
    uncommented = _strip_lean_comments(code)
    if uncommented != code:
        errors.append("classical LDT signature code must not contain comments")
    namespace_prefix = "namespace MIPStarRE.QPBT\n"
    namespace_suffix = "\nend MIPStarRE.QPBT"
    if not code.startswith(namespace_prefix) or not code.endswith(namespace_suffix):
        errors.append("classical LDT signature has incorrect namespace framing")
        return [], {}, errors
    body = uncommented[len(namespace_prefix):-len(namespace_suffix)]
    head = re.compile(
        r"(?m)^(?:noncomputable\s+)?(?:abbrev|def|structure|inductive|theorem)\s+"
        r"([A-Za-z_][A-Za-z0-9_.'?]*)(?=\s|\{)"
    )
    matches = list(head.finditer(body))
    names: list[str] = []
    segments: dict[str, str] = {}
    for position, match in enumerate(matches):
        short_name = match.group(1)
        qualified_name = f"MIPStarRE.QPBT.{short_name}"
        names.append(qualified_name)
        end = matches[position + 1].start() if position + 1 < len(matches) else len(body)
        segments[qualified_name] = body[match.start():end].strip()
    return names, segments, errors


def classical_ldt_signature_errors(
        signature_block: str, expected_hash: str | None = None) -> list[str]:
    """Reject comment-only, weakened, or incomplete F09A API contracts."""
    names, segments, errors = classical_ldt_declaration_segments(signature_block)
    if names != CLASSICAL_LDT_GAME_CORE_LEAN_NAMES:
        errors.append("classical LDT signature declaration names/order must remain exact")
    for qualified_name, expected_digest in (
            CLASSICAL_LDT_GAME_CORE_DECLARATION_SHA256.items()):
        segment = segments.get(qualified_name)
        if segment is None:
            errors.append(
                f"classical LDT signature lacks declaration: {qualified_name}"
            )
        elif hashlib.sha256(segment.encode("utf-8")).hexdigest() != expected_digest:
            errors.append(
                f"classical LDT declaration differs from exact signature: {qualified_name}"
            )
    for term in CLASSICAL_LDT_GAME_CORE_SIGNATURE_REQUIRED_TERMS:
        if term not in signature_block:
            errors.append(f"classical LDT signature omits required term: {term}")
    if signature_block.count("deriving DecidableEq, Fintype") != 3:
        errors.append("classical LDT signature must derive exactly three finite carriers")
    observed_instances = re.findall(
        r"(?m)^noncomputable local instance ([A-Za-z_][A-Za-z0-9_']*)\s+\(k : Nat\)",
        signature_block,
    )
    if observed_instances != CLASSICAL_LDT_LOCAL_INSTANCE_NAMES:
        errors.append("classical LDT local instance names/order must remain exact")
    errors.extend(
        f"classical LDT signature contains forbidden pattern: {pattern}"
        for pattern in CLASSICAL_LDT_GAME_CORE_SIGNATURE_FORBIDDEN_PATTERNS
        if re.search(pattern, signature_block, flags=re.IGNORECASE)
    )
    if expected_hash is None:
        expected_hash = CLASSICAL_LDT_GAME_CORE_IMPLEMENTATION_CONTRACT[
            "signature_manifest"
        ]["sha256"]
    if hashlib.sha256(signature_block.encode("utf-8")).hexdigest() != expected_hash:
        errors.append("classical LDT signature block differs from the exact reviewed API")
    return errors


CLASSICAL_LDT_GAME_CORE_IMPLEMENTATION_CONTRACT = {
    "writer_lane": "game",
    "owned_file": "MIPStarRE/QPBT/Game/ClassicalLDT.lean",
    "imports": ["MIPStarRE.QPBT.Basic.Polynomial", "MIPStarRE.QPBT.Game.Types"],
    "signature_manifest": {
        "path": "workflow/reviews/qpbt-074-game-contract-a01.md",
        "begin_marker": "<!-- BEGIN F09A-SIGNATURES -->",
        "end_marker": "<!-- END F09A-SIGNATURES -->",
        "sha256": "49cdac4cc305006f9bce3679c5f2c5784edf54ab1d2a5cd6685167cfee7a2840",
    },
    "reused_api": [
        "MIPStarRE.QPBT.FieldData.coordinates",
        "MIPStarRE.QPBT.FieldPoint",
        "MIPStarRE.QPBT.FieldVector",
        "MIPStarRE.QPBT.ConditionallyLinearMap",
        "MIPStarRE.QPBT.CLSampler.sample",
        "PMF.map",
        "PMF.uniformOfFintype",
    ],
    "validation_commands": ["lake env lean MIPStarRE/QPBT/Game/ClassicalLDT.lean"],
    "allowed_minimal_sorries": [],
    "proof_complete_sorry_count": 0,
}
CLASSICAL_LDT_ANALYSIS_PREREQUISITES = [
    "F02-CODE", "F03-MEASUREMENT", "F07-TYPED", CLASSICAL_LDT_GAME_CORE_ID,
]
QPBT_GAME_PREREQUISITES = [
    "F02-CODE", "F05-PAULI", "F07-TYPED", MAGIC_GAME_OWNER_ID,
    CLASSICAL_LDT_GAME_CORE_ID, "G01-PARAMETERS",
]
# These digests exclude only the derived closure. Every source-facing field,
# integrity table, declaration, import, disposition, and ownership boundary is fixed.
CLASSICAL_LDT_NODE_CONTRACT_SHA256 = {
    CLASSICAL_LDT_GAME_CORE_ID:
        "840bdcf5ef6d429c3a40a18bbad7ebff24dedf4a6412ca8b343a540a29ea1afe",
    CLASSICAL_LDT_ANALYSIS_ID:
        "ea75ce0aacd9580f5e0cca8928e0751bb82e7bdf93dda5b0821dbde01be6395c",
    QPBT_GAME_ID:
        "656cee6164f038e9487ea5f6deaec3dae15ffcf970638ae2ee600270513d7e70",
}
CLASSICAL_LDT_GAP_CONTRACT_SHA256 = {
    "G22": "7aafc72bbfd306f1aebbc0d31690eb1b5343bb726e69b9f6944828dda5860375",
    "G23": "8794ea7d4047fa3e6a50348ccd332cbb9d86cbda80b8e8d6eb60a5e9cd07e485",
}
CLASSICAL_LDT_AUTHENTICATED_MARKDOWN = {
    Path("workflow/reviews/qpbt-074-game-contract-a01.md"):
        "55c6f9732c72570e0b074a2493658d975adabc44005dab3bd1564f0d0081c23c",
    Path("docs/paper-gaps/canonical-line-zero-direction.md"):
        "59305b0d7cebd023d630fce9985d196ad2807b620d3f16f19991bcbcd9c84555",
}
NON_DETYPING_COMPLEXITY_CONTRACTS = {
    "K03-INTRO-COMPLEXITY": {
        "generated_lines": [73, 84],
        "lean_names": ["MIPStarRE.QPBT.canonicalParameters_complexity"],
    },
    "K04-GAME-COMPLEXITY": {
        "generated_lines": [85, 127],
        "lean_names": ["MIPStarRE.QPBT.pauliBasisGame_complexity"],
    },
}
EXPECTED_TARGETS = {
    "completeness": "G03-COMPLETENESS",
    "soundness": "S01-SOUNDNESS",
    "binary": "B01-BINARY",
    "canonical_complexity": "K04-GAME-COMPLEXITY",
}
TARGET_KEYS = set(EXPECTED_TARGETS)
EXPECTED_TARGET_SPINES = {
    "completeness": ["F08-MAGIC-GAME", "G02-GAME", "G03-COMPLETENESS"],
    "soundness": [
        "F01-FIELD", "F02-CODE", "F03-MEASUREMENT", "F04-DISTANCE",
        "F04-ASYMPTOTIC", "F04-CONSISTENCY", "F04-DISTANCE-LAWS", "F05-PAULI",
        "F06-CL", "F06A-EXECUTABLE-CL", "F07-TYPED", "F08-MAGIC-GAME",
        "F09-LDT-GAME",
        "G01-PARAMETERS", "G02-GAME", "N01-NAIMARK", "A01-INDICATOR", "A03-WIN",
        "A05-EXPANDED", "A07-JOINT", "R01-FIBER", "A08-XZ-LINES",
        "L01-LDT-SOUNDNESS", "R02-AXIS-LDT", "R03-RESTRICTED", "A12-GLOBAL",
        "A13-EXACT-PAULI", "A15-UNITARY", "R05-ROBUSTNESS", "S01-SOUNDNESS",
    ],
    "binary": ["F10-PAULI-BINARY", "S01-SOUNDNESS", "B01-BINARY"],
    "canonical_complexity": [
        "G02-GAME", "K01-CANONICAL", "K03-INTRO-COMPLEXITY",
        "K03A-FIELD-ARITHMETIC", "K03B-LOW-DEGREE-COMPLEXITY",
        "K04-GAME-COMPLEXITY",
    ],
}
MINIMAL_SKELETON_PLAN = {
    "stage": "minimal",
    "sorry_count": 4,
    "sorry_declarations": [
        "MIPStarRE.QPBT.fieldDataOfOddExponent",
        *EXECUTABLE_CL_STAGE_4A_SORRIES,
        "MIPStarRE.QPBT.pauliSoundness",
    ],
    "sorry_reasons": {
        "MIPStarRE.QPBT.fieldDataOfOddExponent": "G16",
        "MIPStarRE.QPBT.ExecutableCLSampler.downsizeCompiler_exists":
            "G19/QPBT-061 compiler-execution debt",
        "MIPStarRE.QPBT.ExecutableCLSampler.downsize_time":
            "G19/QPBT-061 runtime-proof debt",
        "MIPStarRE.QPBT.pauliSoundness": "main-theorem",
    },
    "proof_complete_sorry_count": 0,
}


def f07_finiteness_contract(node: dict[str, Any]) -> dict[str, str]:
    """Extract the source-reviewed F07 finiteness boundary for exact comparison."""
    integrity = node.get("integrity", {})
    return {
        "statement": str(node.get("statement", "")),
        "encoding": str(node.get("encoding", "")),
        "boundary_hypotheses": str(node.get("boundary_hypotheses", "")),
        "paper_assumptions": str(integrity.get("paper_assumptions", "")),
        "lean_assumptions": str(integrity.get("lean_assumptions", "")),
        "lean_conclusion": str(integrity.get("lean_conclusion", "")),
    }


def executable_cl_contract(node: dict[str, Any]) -> dict[str, str]:
    """Extract the source-reviewed executable CL boundary for exact comparison."""
    integrity = node.get("integrity", {})
    return {
        "statement": str(node.get("statement", "")),
        "encoding": str(node.get("encoding", "")),
        "boundary_hypotheses": str(node.get("boundary_hypotheses", "")),
        "paper_assumptions": str(integrity.get("paper_assumptions", "")),
        "lean_assumptions": str(integrity.get("lean_assumptions", "")),
        "paper_conclusion": str(integrity.get("paper_conclusion", "")),
        "lean_conclusion": str(integrity.get("lean_conclusion", "")),
        "verdict": str(integrity.get("verdict", "")),
    }


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def node_contract_sha256(node: dict[str, Any]) -> str:
    """Hash every canonical node field except its mechanically derived closure."""
    contract = {key: value for key, value in node.items()
                if key != "transitive_definitions"}
    return hashlib.sha256(canonical_json(contract).encode("utf-8")).hexdigest()


def authenticated_markdown_errors(repository_root: Path) -> list[str]:
    """Authenticate the source-contract and paper-gap records required by F09A."""
    errors: list[str] = []
    for relative_path, expected_hash in CLASSICAL_LDT_AUTHENTICATED_MARKDOWN.items():
        path = repository_root / relative_path
        if not path.is_file():
            errors.append(f"F09A-LDT-GAME-CORE: authenticated record missing: {relative_path}")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != expected_hash:
            errors.append(f"F09A-LDT-GAME-CORE: authenticated record hash mismatch: {relative_path}")
    errors.extend(classical_ldt_source_manifest_errors(repository_root))
    errors.extend(classical_ldt_combined_import_probe_errors(repository_root))
    return errors


def detyping_authenticated_markdown_errors(repository_root: Path) -> list[str]:
    """Authenticate the source-reviewed F07A executable-boundary record."""
    errors: list[str] = []
    for relative_path, expected_hash in DETYPING_AUTHENTICATED_MARKDOWN.items():
        path = repository_root / relative_path
        if not path.is_file():
            errors.append(
                f"{DETYPING_OWNER_ID}: authenticated paper-gap note missing: {relative_path}"
            )
        elif hashlib.sha256(path.read_bytes()).hexdigest() != expected_hash:
            errors.append(
                f"{DETYPING_OWNER_ID}: authenticated paper-gap note hash mismatch: "
                f"{relative_path}"
            )
    return errors


def classical_ldt_combined_import_probe_errors(repository_root: Path) -> list[str]:
    """Authenticate both collision-sensitive future Verifier import orders."""
    path = repository_root / "workflow/reviews/qpbt-074-game-contract-a01.md"
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    begin, end = CLASSICAL_LDT_COMBINED_IMPORT_PROBE_MARKERS
    if (text.count(begin) != 1 or text.count(end) != 1 or
            text.index(begin) >= text.index(end)):
        return ["F09A-LDT-GAME-CORE: combined-import probe markers must be unique and ordered"]
    block = text.split(begin, 1)[1].split(end, 1)[0].strip()
    if not block.startswith("```json\n") or not block.endswith("\n```"):
        return ["F09A-LDT-GAME-CORE: combined-import probe must use one JSON fence"]
    try:
        observed = json.loads(block[len("```json\n"):-len("\n```")])
    except json.JSONDecodeError:
        return ["F09A-LDT-GAME-CORE: combined-import probe is invalid JSON"]
    if observed != CLASSICAL_LDT_COMBINED_IMPORT_PROBE:
        return ["F09A-LDT-GAME-CORE: combined-import probe must remain exact"]
    return []


def classical_ldt_source_manifest_errors(repository_root: Path) -> list[str]:
    """Parse and authenticate the machine-readable paper inventory in the F09A record."""
    relative_path = Path("workflow/reviews/qpbt-074-game-contract-a01.md")
    path = repository_root / relative_path
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    begin, end = CLASSICAL_LDT_SOURCE_MANIFEST_MARKERS
    if (text.count(begin) != 1 or text.count(end) != 1 or
            text.index(begin) >= text.index(end)):
        return ["F09A-LDT-GAME-CORE: source manifest markers must be unique and ordered"]
    block = text.split(begin, 1)[1].split(end, 1)[0].strip()
    if not block.startswith("```json\n") or not block.endswith("\n```"):
        return ["F09A-LDT-GAME-CORE: source manifest must use one JSON fence"]
    try:
        observed = json.loads(block[len("```json\n"):-len("\n```")])
    except json.JSONDecodeError:
        return ["F09A-LDT-GAME-CORE: source manifest is invalid JSON"]
    errors: list[str] = []
    if observed != CLASSICAL_LDT_GAME_CORE_AUTHENTICATED_SOURCES:
        errors.append("F09A-LDT-GAME-CORE: authenticated source manifest must remain exact")
    if isinstance(observed, list):
        flattened: list[Any] = []
        for source in observed:
            anchors = source.get("anchors") if isinstance(source, dict) else None
            if isinstance(anchors, list):
                flattened.extend(anchors)
        if flattened != CLASSICAL_LDT_GAME_CORE_SOURCE_ANCHORS:
            errors.append("F09A-LDT-GAME-CORE: source manifest anchors must match node anchors")
    return errors


def _duplicates(values: list[str]) -> set[str]:
    seen: set[str] = set()
    return {value for value in values if value in seen or seen.add(value)}


def dependency_ancestors(node_id: str, prerequisites: dict[str, set[str]]) -> set[str]:
    """Return the strict dependency closure, ignoring already-reported unknown IDs."""
    ancestors: set[str] = set()
    stack = list(prerequisites.get(node_id, set()))
    while stack:
        current = stack.pop()
        if current in ancestors or current not in prerequisites:
            continue
        ancestors.add(current)
        stack.extend(prerequisites[current])
    return ancestors


def definition_ancestor_ids(node_id: str, nodes_by_id: dict[str, dict[str, Any]],
                            prerequisites: dict[str, set[str]]) -> list[str]:
    """Definitions used transitively are definition nodes in the strict proof closure."""
    return sorted(
        ancestor for ancestor in dependency_ancestors(node_id, prerequisites)
        if nodes_by_id[ancestor].get("kind") == "definition"
    )


def _source_anchor_errors(node_id: str, field: str, source: Any) -> list[str]:
    """Validate one immutable paper-source anchor without reading its file."""
    prefix = f"{node_id}: {field}"
    if not isinstance(source, dict) or set(source) != SOURCE_KEYS:
        return [f"{prefix} must use the exact four-field schema"]
    errors: list[str] = []
    for key in ("generated_lines", "original_lines"):
        span = source[key]
        if not (isinstance(span, list) and len(span) == 2 and
                all(isinstance(x, int) and x > 0 for x in span) and span[0] <= span[1]):
            errors.append(f"{node_id}: invalid {field}.{key}")
    raw_path = source["path"]
    if not isinstance(raw_path, str):
        errors.append(f"{node_id}: unsafe/non-TeX {field} path")
    else:
        path = Path(raw_path)
        if path.is_absolute() or ".." in path.parts or path.suffix != ".tex":
            errors.append(f"{node_id}: unsafe/non-TeX {field} path")
    if not isinstance(source["label"], str):
        errors.append(f"{node_id}: invalid {field}.label")
    return errors


def source_anchors(node: dict[str, Any]) -> list[tuple[str, Any]]:
    """Return the primary anchor followed by any independently cited ranges."""
    anchors = [("source", node.get("source"))]
    additional = node.get("additional_sources", [])
    if isinstance(additional, list):
        anchors.extend((f"additional_sources[{index}]", source)
                       for index, source in enumerate(additional))
    return anchors


def _implementation_contract_errors(node: dict[str, Any],
                                    skeleton_plan: dict[str, Any]) -> list[str]:
    """Validate a machine-visible contract that can be issued without inference."""
    node_id = node["id"]
    contract = node.get("implementation_contract")
    if contract is None:
        return []
    if not isinstance(contract, dict) or set(contract) != IMPLEMENTATION_CONTRACT_KEYS:
        return [f"{node_id}: implementation_contract has incorrect schema"]
    errors: list[str] = []
    if contract["writer_lane"] not in IMPLEMENTATION_WRITER_LANES:
        errors.append(f"{node_id}: invalid implementation writer lane")
    owned_file = contract["owned_file"]
    if not isinstance(owned_file, str):
        errors.append(f"{node_id}: invalid implementation owned file")
    else:
        owned_path = Path(owned_file)
        if (owned_path.is_absolute() or ".." in owned_path.parts or
                owned_path.suffix != ".lean" or owned_path.parts[:2] != ("MIPStarRE", "QPBT")):
            errors.append(f"{node_id}: invalid implementation owned file")
    for field in ("imports", "reused_api", "validation_commands",
                  "allowed_minimal_sorries"):
        values = contract[field]
        if not isinstance(values, list) or any(not isinstance(value, str) or not value
                                               for value in values):
            errors.append(f"{node_id}: implementation {field} must be a string list")
        elif _duplicates(values):
            errors.append(f"{node_id}: implementation {field} contains duplicates")
    imports = contract["imports"]
    if isinstance(imports, list) and not imports:
        errors.append(f"{node_id}: implementation imports must be nonempty")
    manifest = contract["signature_manifest"]
    signature_block: str | None = None
    if not isinstance(manifest, dict) or set(manifest) != SIGNATURE_MANIFEST_KEYS:
        errors.append(f"{node_id}: implementation signature_manifest has incorrect schema")
    else:
        raw_path = manifest["path"]
        if not isinstance(raw_path, str):
            errors.append(f"{node_id}: invalid signature manifest path")
        else:
            manifest_path = Path(raw_path)
            if (manifest_path.is_absolute() or ".." in manifest_path.parts or
                    manifest_path.suffix != ".md" or
                    manifest_path.parts[:2] != ("workflow", "reviews")):
                errors.append(f"{node_id}: invalid signature manifest path")
            else:
                absolute_path = ROOT.parent / manifest_path
                if not absolute_path.is_file():
                    errors.append(f"{node_id}: signature manifest file does not exist")
                else:
                    manifest_text = absolute_path.read_text(encoding="utf-8")
                    begin = manifest["begin_marker"]
                    end = manifest["end_marker"]
                    if (not isinstance(begin, str) or not begin or
                            not isinstance(end, str) or not end or begin == end):
                        errors.append(f"{node_id}: invalid signature manifest markers")
                    elif (manifest_text.count(begin) != 1 or
                          manifest_text.count(end) != 1 or
                          manifest_text.index(begin) >= manifest_text.index(end)):
                        errors.append(f"{node_id}: signature manifest markers must be unique and ordered")
                    else:
                        signature_block = manifest_text.split(begin, 1)[1].split(end, 1)[0].strip()
                        expected_hash = manifest["sha256"]
                        if not (isinstance(expected_hash, str) and
                                re.fullmatch(r"[0-9a-f]{64}", expected_hash)):
                            errors.append(f"{node_id}: invalid signature manifest SHA-256")
                        elif hashlib.sha256(signature_block.encode("utf-8")).hexdigest() != expected_hash:
                            errors.append(f"{node_id}: signature manifest hash mismatch")
    if signature_block is not None:
        for name in node["lean"]["names"]:
            short_name = name.rsplit(".", 1)[-1]
            if not re.search(rf"\b{re.escape(short_name)}\b", signature_block):
                errors.append(f"{node_id}: signature manifest omits planned declaration {name}")
        if node_id == EXECUTABLE_CL_OWNER_ID:
            errors.extend(
                f"{node_id}: {error}"
                for error in executable_cl_signature_errors(signature_block)
            )
        if node_id == CLASSICAL_LDT_GAME_CORE_ID:
            errors.extend(
                f"{node_id}: {error}"
                for error in classical_ldt_signature_errors(signature_block)
            )
    validation_commands = contract["validation_commands"]
    if isinstance(validation_commands, list) and isinstance(owned_file, str):
        scoped_command = f"lake env lean {owned_file}"
        if scoped_command not in validation_commands:
            errors.append(f"{node_id}: implementation validation omits scoped Lean command")
    allowed_sorries = contract["allowed_minimal_sorries"]
    declared_sorries = set(skeleton_plan.get("sorry_declarations", []))
    if isinstance(allowed_sorries, list):
        unknown = set(allowed_sorries) - declared_sorries
        if unknown:
            errors.append(f"{node_id}: implementation permits undeclared sorries {sorted(unknown)}")
        private_sorries = (
            set(EXECUTABLE_CL_PRIVATE_STAGE_4A_SORRIES)
            if node_id == EXECUTABLE_CL_OWNER_ID else set()
        )
        foreign = set(allowed_sorries) - set(node["lean"]["names"]) - private_sorries
        if foreign:
            errors.append(f"{node_id}: implementation permits foreign sorries {sorted(foreign)}")
    if contract["proof_complete_sorry_count"] != 0:
        errors.append(f"{node_id}: proof-complete implementation must permit zero sorries")
    return errors


def validate_data(nodes_doc: dict[str, Any], gaps_doc: dict[str, Any],
                  externals_doc: dict[str, Any]) -> list[str]:
    errors = (executable_cl_historical_report_errors(ROOT.parent) +
              authenticated_markdown_errors(ROOT.parent) +
              detyping_authenticated_markdown_errors(ROOT.parent))
    if nodes_doc.get("schema_version") != 1:
        errors.append("nodes schema_version must be 1")
    nodes = nodes_doc.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        return errors + ["nodes must be a nonempty list"]
    gaps = gaps_doc.get("gaps", [])
    externals = externals_doc.get("sources", [])
    if gaps_doc.get("schema_version") != 1:
        errors.append("gaps schema_version must be 1")
    if externals_doc.get("schema_version") != 1:
        errors.append("external-sources schema_version must be 1")
    gap_ids = {gap.get("id") for gap in gaps}
    external_ids = {source.get("id") for source in externals}
    for duplicate in sorted(_duplicates([gap.get("id") for gap in gaps if isinstance(gap.get("id"), str)])):
        errors.append(f"duplicate gap id: {duplicate}")
    for duplicate in sorted(_duplicates([source.get("id") for source in externals
                                         if isinstance(source.get("id"), str)])):
        errors.append(f"duplicate external id: {duplicate}")
    ids = [node.get("id") for node in nodes]
    for duplicate in sorted(_duplicates([x for x in ids if isinstance(x, str)])):
        errors.append(f"duplicate node id: {duplicate}")
    node_ids = set(ids)
    lean_names: list[str] = []
    for node in nodes:
        node_id = node.get("id", "<missing>")
        missing = REQUIRED_NODE_KEYS - set(node)
        if missing:
            errors.append(f"{node_id}: missing keys {sorted(missing)}")
            continue
        if node["chapter"] not in CHAPTERS:
            errors.append(f"{node_id}: invalid chapter {node['chapter']!r}")
        if node["status"] not in STATUSES:
            errors.append(f"{node_id}: invalid status {node['status']!r}")
        if node["fidelity"] not in FIDELITIES:
            errors.append(f"{node_id}: invalid fidelity {node['fidelity']!r}")
        if node["kind"] not in KINDS:
            errors.append(f"{node_id}: invalid kind {node['kind']!r}")
        errors.extend(_source_anchor_errors(node_id, "source", node["source"]))
        if "additional_sources" in node:
            additional = node["additional_sources"]
            if not isinstance(additional, list) or not additional:
                errors.append(f"{node_id}: additional_sources must be a nonempty list")
            else:
                for field, source in source_anchors(node)[1:]:
                    errors.extend(_source_anchor_errors(node_id, field, source))
                serialized = [canonical_json(source) for _, source in source_anchors(node)
                              if isinstance(source, dict)]
                if _duplicates(serialized):
                    errors.append(f"{node_id}: duplicate source anchor")
        errors.extend(_implementation_contract_errors(node, nodes_doc.get("skeleton_plan", {})))
        lean = node["lean"]
        if set(lean) != {"module", "names"} or not lean["module"].startswith("MIPStarRE.QPBT"):
            errors.append(f"{node_id}: invalid Lean plan")
        elif not isinstance(lean["names"], list) or not lean["names"]:
            errors.append(f"{node_id}: Lean names must be nonempty")
        else:
            lean_names.extend(lean["names"])
        for field in ("transitive_definitions", "prerequisites"):
            if not isinstance(node[field], list):
                errors.append(f"{node_id}: {field} must be a list")
                continue
            for dep in node[field]:
                if dep not in node_ids:
                    errors.append(f"{node_id}: unknown {field} node {dep}")
        if node_id in node["prerequisites"]:
            errors.append(f"{node_id}: self dependency")
        unknown_gaps = set(node["gap_ids"]) - gap_ids
        if unknown_gaps:
            errors.append(f"{node_id}: unknown gaps {sorted(unknown_gaps)}")
        for gap_id in set(node["gap_ids"]) & gap_ids:
            gap = next(item for item in gaps if item.get("id") == gap_id)
            if node_id not in gap.get("affected_nodes", []):
                errors.append(f"{node_id}: gap {gap_id} lacks reciprocal affected-node link")
        if node["fidelity"] == "repaired-internal" and not node["gap_ids"]:
            errors.append(f"{node_id}: repaired internal node must cite a gap")
        if node["status"] == "paper-gap" and not node["gap_ids"]:
            errors.append(f"{node_id}: paper-gap status must cite a gap")
        if node["kind"] == "external-theorem":
            external_id = node.get("external_id")
            if external_id not in external_ids:
                errors.append(f"{node_id}: missing/unknown external_id")
        integrity = node["integrity"]
        if node["public"] or node["kind"] in {"theorem", "lemma", "corollary"}:
            required_integrity = {"paper_assumptions", "lean_assumptions", "paper_conclusion",
                                  "lean_conclusion", "verdict"}
            if not isinstance(integrity, dict) or set(integrity) != required_integrity:
                errors.append(f"{node_id}: paper-facing entry needs an exact integrity table")
            elif integrity["verdict"] not in {"exact", "faithful boundary", "documented mismatch"}:
                errors.append(f"{node_id}: invalid integrity verdict")
    for duplicate in sorted(_duplicates(lean_names)):
        errors.append(f"duplicate planned Lean declaration: {duplicate}")

    for gap in gaps:
        required = {"id", "class", "source", "affected_nodes", "paper_problem",
                    "disposition", "public_effect", "issue"}
        if set(gap) != required:
            errors.append(f"gap {gap.get('id')}: incorrect schema")
        for node_id in gap.get("affected_nodes", []):
            if node_id not in node_ids:
                errors.append(f"gap {gap.get('id')}: unknown affected node {node_id}")
            elif gap.get("id") not in next(n for n in nodes if n["id"] == node_id)["gap_ids"]:
                errors.append(f"gap {gap.get('id')}: missing reciprocal link from {node_id}")
    for source in externals:
        allowed_keys = EXTERNAL_KEYS | {"pin_contract"}
        if not EXTERNAL_KEYS <= set(source) or not set(source) <= allowed_keys:
            errors.append(f"external {source.get('id')}: incorrect schema")
        arxiv = str(source.get("arxiv", ""))
        match = re.fullmatch(r"\d{4}\.\d{4,5}(v\d+)", arxiv)
        if not match:
            errors.append(f"external {source.get('id')}: arXiv version is not exact")
        else:
            if source.get("version") != match.group(1):
                errors.append(f"external {source.get('id')}: version disagrees with arXiv ID")
            if source.get("url") != f"https://arxiv.org/abs/{arxiv}":
                errors.append(f"external {source.get('id')}: URL disagrees with arXiv ID")
        contract = source.get("pin_contract")
        if source.get("status") == "pinned-published" and contract is None:
            errors.append(f"external {source.get('id')}: published pin requires a pin contract")
        if contract is not None:
            if not isinstance(contract, dict) or set(contract) != PIN_CONTRACT_KEYS:
                errors.append(f"external {source.get('id')}: invalid pin contract schema")
            elif not match or any((
                contract["authority"] != "arXiv",
                contract["versioned_id"] != arxiv,
                contract["metadata_url"] != f"https://arxiv.org/abs/{arxiv}",
                contract["source_url"] != f"https://arxiv.org/src/{arxiv}",
                not re.fullmatch(r"\d{4}-\d{2}-\d{2}", contract["last_revised"]),
                contract["release"] != "published-version",
                contract["verification_basis"] != "official arXiv metadata",
            )):
                errors.append(f"external {source.get('id')}: pin contract disagrees with source")
    externals_by_id = {source.get("id"): source for source in externals}
    for source_id, expected in AUTHORITATIVE_EXTERNAL_SOURCES.items():
        source = externals_by_id.get(source_id)
        if source is None:
            errors.append(f"authoritative external source missing: {source_id}")
            continue
        observed = {key: source.get(key) for key in expected}
        if observed != expected:
            errors.append(f"external {source_id}: authoritative contract must remain exact")

    prerequisites = {node["id"]: set(node["prerequisites"]) for node in nodes}
    nodes_by_id = {node["id"]: node for node in nodes}
    game_semantics = nodes_by_id.get(GAME_SEMANTICS_OWNER_ID)
    if game_semantics is None:
        errors.append(f"missing exact game-semantics owner {GAME_SEMANTICS_OWNER_ID}")
    else:
        observed_anchors = [game_semantics.get("source"),
                            *game_semantics.get("additional_sources", [])]
        if observed_anchors != GAME_SEMANTICS_SOURCE_ANCHORS:
            errors.append(
                f"{GAME_SEMANTICS_OWNER_ID}: game-semantics source ranges must remain exact"
            )
        if game_semantics["prerequisites"] != GAME_SEMANTICS_PREREQUISITES:
            errors.append(
                f"{GAME_SEMANTICS_OWNER_ID}: game-semantics prerequisites must remain exact"
            )
        if game_semantics["lean"].get("names") != GAME_SEMANTICS_LEAN_NAMES:
            errors.append(
                f"{GAME_SEMANTICS_OWNER_ID}: game-semantics callable names must remain exact"
            )
    magic_game = nodes_by_id.get(MAGIC_GAME_OWNER_ID)
    if magic_game is None:
        errors.append(f"missing exact Magic Square game owner {MAGIC_GAME_OWNER_ID}")
    elif magic_game.get("prerequisites") != MAGIC_GAME_PREREQUISITES:
        errors.append(
            f"{MAGIC_GAME_OWNER_ID}: F04A game-semantics direct prerequisite must remain exact"
        )
    detyping = nodes_by_id.get(DETYPING_OWNER_ID)
    if detyping is None:
        errors.append(f"missing exact detyping owner {DETYPING_OWNER_ID}")
    else:
        observed_anchors = [detyping.get("source"),
                            *detyping.get("additional_sources", [])]
        if observed_anchors != DETYPING_SOURCE_ANCHORS:
            errors.append(f"{DETYPING_OWNER_ID}: detyping source anchors must remain exact")
        if detyping["prerequisites"] != DETYPING_PREREQUISITES:
            errors.append(f"{DETYPING_OWNER_ID}: detyping prerequisites must remain exact")
        if detyping["lean"].get("names") != DETYPING_LEAN_NAMES:
            errors.append(f"{DETYPING_OWNER_ID}: detyping callable names must remain exact")
        if detyping.get("gap_ids") != DETYPING_GAP_IDS:
            errors.append(f"{DETYPING_OWNER_ID}: paper-gap linkage must remain exact")
        if (detyping.get("fidelity") != "repaired-internal" or
                detyping.get("integrity", {}).get("verdict") != "documented mismatch"):
            errors.append(
                f"{DETYPING_OWNER_ID}: documented-mismatch fidelity must remain exact"
            )
        integrity_hash = hashlib.sha256(
            canonical_json(detyping.get("integrity")).encode("utf-8")
        ).hexdigest()
        if integrity_hash != DETYPING_INTEGRITY_SHA256:
            errors.append(
                f"{DETYPING_OWNER_ID}: statement-integrity table must remain exact"
            )
        if node_contract_sha256(detyping) != DETYPING_NODE_CONTRACT_SHA256:
            errors.append(
                f"{DETYPING_OWNER_ID}: source-reviewed semantic contract must remain exact"
            )
    f06 = nodes_by_id.get("F06-CL", {})
    if "MIPStarRE.QPBT.CLSampler.sample_directSum" not in f06.get("lean", {}).get("names", []):
        errors.append("F06-CL: direct-sum product-distribution theorem must remain callable")
    if f06.get("source") != F06_SOURCE_ANCHOR:
        errors.append("F06-CL: mathematical source range must end exactly at line 552")
    if (f06.get("fidelity") != "faithful-boundary" or
            f06.get("integrity", {}).get("verdict") != "faithful boundary"):
        errors.append("F06-CL: fidelity must match its faithful-boundary integrity verdict")
    f06_boundary = str(f06.get("boundary_hypotheses", "")).lower()
    if not all(term in f06_boundary for term in F06_EXECUTABLE_OWNER_TERMS):
        errors.append(
            "F06-CL: generic executable ownership must remain assigned only to F06A"
        )
    executable_cl = nodes_by_id.get(EXECUTABLE_CL_OWNER_ID)
    if executable_cl is None:
        errors.append(f"missing exact executable CL owner {EXECUTABLE_CL_OWNER_ID}")
    else:
        observed_anchors = [executable_cl.get("source"),
                            *executable_cl.get("additional_sources", [])]
        if observed_anchors != EXECUTABLE_CL_SOURCE_ANCHORS:
            errors.append(
                f"{EXECUTABLE_CL_OWNER_ID}: executable CL source anchors must remain exact"
            )
        if executable_cl.get("prerequisites") != EXECUTABLE_CL_PREREQUISITES:
            errors.append(
                f"{EXECUTABLE_CL_OWNER_ID}: executable CL prerequisites must remain exact"
            )
        if executable_cl.get("lean", {}).get("module") != "MIPStarRE.QPBT.Game.Types":
            errors.append(
                f"{EXECUTABLE_CL_OWNER_ID}: executable CL module must remain exact"
            )
        if executable_cl.get("lean", {}).get("names") != EXECUTABLE_CL_LEAN_NAMES:
            errors.append(
                f"{EXECUTABLE_CL_OWNER_ID}: executable CL callable names must remain exact"
            )
        if executable_cl.get("implementation_contract") != (
                EXECUTABLE_CL_IMPLEMENTATION_CONTRACT):
            errors.append(
                f"{EXECUTABLE_CL_OWNER_ID}: implementation contract must remain exact"
            )
        if (executable_cl.get("kind") != "definition" or
                executable_cl.get("fidelity") != "faithful-boundary"):
            errors.append(
                f"{EXECUTABLE_CL_OWNER_ID}: node kind and fidelity must remain exact"
            )
        if executable_cl_contract(executable_cl) != EXECUTABLE_CL_CONTRACT:
            errors.append(
                f"{EXECUTABLE_CL_OWNER_ID}: executable CL semantic contract must remain exact"
            )
    f07 = nodes_by_id.get("F07-TYPED", {})
    if f07.get("source") != TYPED_SOURCE_ANCHOR:
        errors.append("F07-TYPED: typed source range must remain exact")
    if f07.get("prerequisites") != TYPED_PREREQUISITES:
        errors.append("F07-TYPED: executable CL prerequisite must remain exact")
    if f07.get("lean", {}).get("names") != TYPED_LEAN_NAMES:
        errors.append("F07-TYPED: typed callable names must remain exact")
    if f07_finiteness_contract(f07) != F07_FINITENESS_CONTRACT:
        errors.append(
            "F07-TYPED: generic dependent-fiber finiteness contract must remain exact"
        )
    classical_ldt_core = nodes_by_id.get(CLASSICAL_LDT_GAME_CORE_ID)
    if classical_ldt_core is None:
        errors.append(f"missing exact classical-LDT game core {CLASSICAL_LDT_GAME_CORE_ID}")
    else:
        observed_anchors = [classical_ldt_core.get("source"),
                            *classical_ldt_core.get("additional_sources", [])]
        if observed_anchors != CLASSICAL_LDT_GAME_CORE_SOURCE_ANCHORS:
            errors.append(
                f"{CLASSICAL_LDT_GAME_CORE_ID}: source ranges must remain exact"
            )
        if classical_ldt_core.get("prerequisites") != (
                CLASSICAL_LDT_GAME_CORE_PREREQUISITES):
            errors.append(
                f"{CLASSICAL_LDT_GAME_CORE_ID}: prerequisites must remain exact"
            )
        if classical_ldt_core.get("lean", {}).get("module") != (
                "MIPStarRE.QPBT.Game.ClassicalLDT"):
            errors.append(
                f"{CLASSICAL_LDT_GAME_CORE_ID}: must remain in the Game layer"
            )
        if classical_ldt_core.get("lean", {}).get("names") != (
                CLASSICAL_LDT_GAME_CORE_LEAN_NAMES):
            errors.append(
                f"{CLASSICAL_LDT_GAME_CORE_ID}: public declaration and law names must remain exact"
            )
        if classical_ldt_core.get("implementation_contract") != (
                CLASSICAL_LDT_GAME_CORE_IMPLEMENTATION_CONTRACT):
            errors.append(
                f"{CLASSICAL_LDT_GAME_CORE_ID}: implementation contract must remain exact"
            )
        forbidden_ancestors = (dependency_ancestors(
            CLASSICAL_LDT_GAME_CORE_ID, prerequisites
        ) & CLASSICAL_LDT_FORBIDDEN_ANCESTORS)
        if forbidden_ancestors:
            errors.append(
                f"{CLASSICAL_LDT_GAME_CORE_ID}: forbidden F06A/F07 semantic ancestors "
                f"{sorted(forbidden_ancestors)}"
            )
        f06_names = set(nodes_by_id.get("F06-CL", {}).get("lean", {}).get("names", []))
        if not set(CLASSICAL_LDT_GAME_CORE_F06_REUSED_API) <= f06_names:
            errors.append(
                f"{CLASSICAL_LDT_GAME_CORE_ID}: co-located reused API must be owned by F06"
            )
        reused_api = classical_ldt_core.get("implementation_contract", {}).get(
            "reused_api", []
        )
        observed_f06_reused = [name for name in reused_api if name in f06_names]
        if observed_f06_reused != CLASSICAL_LDT_GAME_CORE_F06_REUSED_API:
            errors.append(
                f"{CLASSICAL_LDT_GAME_CORE_ID}: F06-only reused API whitelist must remain exact"
            )
    classical_ldt_analysis = nodes_by_id.get(CLASSICAL_LDT_ANALYSIS_ID)
    if classical_ldt_analysis is None:
        errors.append(f"missing exact classical-LDT analysis owner {CLASSICAL_LDT_ANALYSIS_ID}")
    else:
        if classical_ldt_analysis.get("prerequisites") != (
                CLASSICAL_LDT_ANALYSIS_PREREQUISITES):
            errors.append(
                f"{CLASSICAL_LDT_ANALYSIS_ID}: F09A direct prerequisite must remain exact"
            )
        if classical_ldt_analysis.get("lean", {}).get("module") != (
                "MIPStarRE.QPBT.Analysis.ClassicalLDTAdapter"):
            errors.append(
                f"{CLASSICAL_LDT_ANALYSIS_ID}: must remain in the downstream Analysis layer"
            )
    qpbt_game = nodes_by_id.get(QPBT_GAME_ID)
    if qpbt_game is None:
        errors.append(f"missing exact QPBT game owner {QPBT_GAME_ID}")
    else:
        if qpbt_game.get("prerequisites") != QPBT_GAME_PREREQUISITES:
            errors.append(
                f"{QPBT_GAME_ID}: F09A direct prerequisite must remain exact"
            )
        if qpbt_game.get("lean", {}).get("module") != "MIPStarRE.QPBT.Game.Verifier":
            errors.append(f"{QPBT_GAME_ID}: must remain in the Game layer")
        if (qpbt_game.get("status") != "not-started" or
                qpbt_game.get("fidelity") != "faithful-boundary"):
            errors.append(
                f"{QPBT_GAME_ID}: progress and inherited G22/G23 fidelity must remain exact"
            )
    for node_id, expected_hash in CLASSICAL_LDT_NODE_CONTRACT_SHA256.items():
        node = nodes_by_id.get(node_id)
        if node is not None and node_contract_sha256(node) != expected_hash:
            errors.append(f"{node_id}: source-reviewed semantic contract must remain exact")
    gaps_by_id = {gap.get("id"): gap for gap in gaps}
    for gap_id, expected_hash in CLASSICAL_LDT_GAP_CONTRACT_SHA256.items():
        gap = gaps_by_id.get(gap_id)
        if gap is None:
            errors.append(f"missing exact classical-LDT paper gap {gap_id}")
        elif hashlib.sha256(canonical_json(gap).encode("utf-8")).hexdigest() != expected_hash:
            errors.append(f"{gap_id}: source range and disposition must remain exact")
    for gap_id, expected_hash in DETYPING_GAP_CONTRACT_SHA256.items():
        gap = gaps_by_id.get(gap_id)
        if gap is None:
            errors.append(f"missing exact detyping paper gap {gap_id}")
        elif hashlib.sha256(canonical_json(gap).encode("utf-8")).hexdigest() != expected_hash:
            errors.append(f"{gap_id}: source range and disposition must remain exact")
    for node_id, expected_contract in NON_DETYPING_COMPLEXITY_CONTRACTS.items():
        node = nodes_by_id.get(node_id, {})
        if node.get("source", {}).get("generated_lines") != expected_contract["generated_lines"]:
            errors.append(f"{node_id}: non-detyping source range must remain exact")
        if node.get("lean", {}).get("names") != expected_contract["lean_names"]:
            errors.append(f"{node_id}: non-detyping callable ownership must remain exact")
        ownership_text = " ".join(str(node.get(field, "")) for field in (
            "statement", "encoding", "boundary_hypotheses"
        )).lower()
        if "detyp" in ownership_text:
            errors.append(f"{node_id}: must not own detyping")
    for node in nodes:
        expected = definition_ancestor_ids(node["id"], nodes_by_id, prerequisites)
        if node["transitive_definitions"] != expected:
            errors.append(
                f"{node['id']}: transitive_definitions must equal definition-ancestor closure "
                f"{expected}"
            )
    pending = copy.deepcopy(prerequisites)
    while pending:
        ready = sorted(node_id for node_id, deps in pending.items() if not deps)
        if not ready:
            errors.append(f"dependency cycle among {sorted(pending)}")
            break
        for node_id in ready:
            pending.pop(node_id)
        for deps in pending.values():
            deps.difference_update(ready)
    targets = nodes_doc.get("targets", {})
    if not isinstance(targets, dict) or set(targets) != TARGET_KEYS:
        errors.append(f"targets must use the exact keys {sorted(TARGET_KEYS)}")
        targets = targets if isinstance(targets, dict) else {}
    if targets != EXPECTED_TARGETS:
        errors.append("targets must preserve the canonical target contract")
    target_spines = nodes_doc.get("required_target_spines", {})
    if not isinstance(target_spines, dict) or set(target_spines) != TARGET_KEYS:
        errors.append(f"required_target_spines must use the exact keys {sorted(TARGET_KEYS)}")
        target_spines = target_spines if isinstance(target_spines, dict) else {}
    if target_spines != EXPECTED_TARGET_SPINES:
        errors.append("required_target_spines must preserve the canonical reachability contract")
    for target_name in sorted(TARGET_KEYS):
        target = targets.get(target_name)
        if target not in node_ids:
            errors.append(f"targets.{target_name} must name an existing node")
            continue
        required_spine = target_spines.get(target_name)
        if not (isinstance(required_spine, list) and
                all(isinstance(node_id, str) and node_id in node_ids
                    for node_id in required_spine)):
            errors.append(f"required_target_spines.{target_name} must list existing nodes")
            continue
        ancestors = dependency_ancestors(target, prerequisites) | {target}
        missing_spine = set(required_spine) - ancestors
        if missing_spine:
            errors.append(
                f"{target_name} target misses required spine {sorted(missing_spine)}"
            )
        for node_id in sorted(ancestors):
            node = nodes_by_id[node_id]
            if node.get("kind") != "external-theorem":
                continue
            external = externals_by_id.get(node.get("external_id"), {})
            if external.get("status") not in RESOLVED_EXTERNAL_STATUSES:
                errors.append(
                    f"{node_id}: {target_name}-critical external source "
                    f"{node.get('external_id')} is unresolved"
                )
    if nodes_doc.get("skeleton_plan") != MINIMAL_SKELETON_PLAN:
        errors.append("skeleton_plan must encode the exact minimal-skeleton proof debt")
    return errors


def split_index(source_root: Path) -> dict[str, tuple[int, int]]:
    manifest = load_json(source_root / "split-manifest.json")
    index: dict[str, tuple[int, int]] = {}
    for collection in manifest["collections"]:
        directory = collection["output_directory"]
        for entry in collection["slices"]:
            slice_id, start, end = entry[:3]
            index[f"references/2001.04383v3/sections/{directory}/{slice_id}.tex"] = (start, end)
    return index


def validate_sources(nodes_doc: dict[str, Any], source_root: Path) -> list[str]:
    errors: list[str] = []
    manifest = source_root / "split-manifest.json"
    if not manifest.is_file():
        return [f"source root lacks split manifest: {manifest}"]
    index = split_index(source_root)
    prefix = "references/2001.04383v3/"
    for node in nodes_doc["nodes"]:
        node_id = node["id"]
        for field, source in source_anchors(node):
            if _source_anchor_errors(node_id, field, source):
                continue
            display = node_id if field == "source" else f"{node_id} {field}"
            path = source["path"]
            if path not in index:
                errors.append(f"{display}: source path absent from split manifest: {path}")
                continue
            relative = path.removeprefix(prefix)
            materialized = source_root / relative
            if not materialized.is_file():
                errors.append(f"{display}: materialized source missing: {materialized}")
                continue
            lines = materialized.read_bytes().splitlines()
            lo, hi = source["generated_lines"]
            if hi > len(lines):
                errors.append(f"{display}: generated line range exceeds file")
                continue
            manifest_start, manifest_end = index[path]
            expected_original = [manifest_start + lo - 1, manifest_start + hi - 1]
            if source["original_lines"] != expected_original or expected_original[1] > manifest_end:
                errors.append(f"{display}: original/generated line mapping mismatch")
            label = source["label"]
            if label:
                needle = f"\\label{{{label}}}".encode("utf-8")
                if not any(needle in line for line in lines[lo - 1:hi]):
                    errors.append(f"{display}: label {label} absent from anchored range")
    if any(node.get("id") == CLASSICAL_LDT_GAME_CORE_ID for node in nodes_doc["nodes"]):
        for path, expected_digest in CLASSICAL_LDT_GAME_CORE_SOURCE_SHA256.items():
            materialized = source_root / path.removeprefix(prefix)
            if not materialized.is_file():
                errors.append(
                    f"{CLASSICAL_LDT_GAME_CORE_ID}: authenticated source missing: {materialized}"
                )
            elif hashlib.sha256(materialized.read_bytes()).hexdigest() != expected_digest:
                errors.append(
                    f"{CLASSICAL_LDT_GAME_CORE_ID}: authenticated source digest mismatch: {path}"
                )
    return errors


def graph_document(nodes_doc: dict[str, Any]) -> dict[str, Any]:
    nodes = nodes_doc["nodes"]
    nodes_by_id = {node["id"]: node for node in nodes}
    prerequisites = {node["id"]: set(node["prerequisites"]) for node in nodes}
    consumers: dict[str, list[str]] = defaultdict(list)
    indegree = {node["id"]: len(node["prerequisites"]) for node in nodes}
    successors: dict[str, list[str]] = defaultdict(list)
    for node in nodes:
        for dep in node["prerequisites"]:
            consumers[dep].append(node["id"])
            successors[dep].append(node["id"])
    ready = sorted(node_id for node_id, degree in indegree.items() if degree == 0)
    order: list[str] = []
    while ready:
        current = ready.pop(0)
        order.append(current)
        for child in sorted(successors[current]):
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
                ready.sort()
    rendered = []
    for node in nodes:
        item = copy.deepcopy(node)
        item["transitive_definitions"] = definition_ancestor_ids(
            node["id"], nodes_by_id, prerequisites
        )
        item["consumers"] = sorted(consumers[node["id"]])
        rendered.append(item)
    return {
        "schema_version": 1,
        "source": "metadata/nodes.json",
        "source_sha256": hashlib.sha256(canonical_json(nodes_doc).encode()).hexdigest(),
        "targets": nodes_doc["targets"],
        "topological_order": order,
        "nodes": sorted(rendered, key=lambda n: n["id"]),
    }


def tex_escape(value: str) -> str:
    replacements = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
                    "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
                    "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
    return "".join(replacements.get(char, char) for char in value)


def join_values(values: list[str]) -> str:
    return ", ".join(values) if values else "none"


def tex_identifier(value: str) -> str:
    return rf"\BlueprintIdentifier{{{tex_escape(value)}}}"


def tex_breakable(value: str) -> str:
    """Render long metadata with discretionary breaks at sequence characters."""
    return rf"\seqsplit{{{tex_escape(value)}}}"


def render_lean_plan(lean: dict[str, Any]) -> str:
    names = r",\linebreak ".join(tex_identifier(name) for name in lean["names"])
    return f"{tex_identifier(lean['module'])}:\\linebreak {names}"


def render_source_anchor(source: dict[str, Any]) -> str:
    """Render one source anchor with both split and original line coordinates."""
    return (f"{source['path']}:{source['generated_lines'][0]}-{source['generated_lines'][1]} "
            f"[original {source['original_lines'][0]}-{source['original_lines'][1]}], "
            f"label {source['label'] or 'none'}")


def render_entry(node: dict[str, Any], consumers: list[str]) -> str:
    source = node["source"]
    lean = node["lean"]
    integrity = node["integrity"]
    fields = [
        ("Source", render_source_anchor(source)),
        ("Statement", node["statement"]),
        ("Lean plan", render_lean_plan(lean)),
        ("Transitive definitions", join_values(node["transitive_definitions"])),
        ("Prerequisites", join_values(node["prerequisites"])),
        ("Consumers", join_values(consumers)),
        ("Encoding", node["encoding"]),
        ("Boundary hypotheses", node["boundary_hypotheses"]),
        ("Status", f"{node['status']}; {node['fidelity']}; gaps {join_values(node['gap_ids'])}"),
    ]
    if node.get("additional_sources"):
        fields.insert(1, ("Additional sources", "; ".join(
            render_source_anchor(source) for source in node["additional_sources"]
        )))
    contract = node.get("implementation_contract")
    if contract:
        signature_manifest = contract["signature_manifest"]
        fields.extend([
            ("Writer lane", contract["writer_lane"]),
            ("Owned Lean file", contract["owned_file"]),
            ("Exact imports", join_values(contract["imports"])),
            ("Signature manifest",
             f"{signature_manifest['path']} [{signature_manifest['sha256']}]"),
            ("Scoped validation", join_values(contract["validation_commands"])),
            ("Allowed minimal sorries", join_values(contract["allowed_minimal_sorries"])),
            ("Proof-complete sorries", contract["proof_complete_sorry_count"]),
        ])
    if integrity:
        fields.extend([
            ("Paper assumptions", integrity["paper_assumptions"]),
            ("Lean assumptions", integrity["lean_assumptions"]),
            ("Paper conclusion", integrity["paper_conclusion"]),
            ("Lean conclusion", integrity["lean_conclusion"]),
            ("Integrity verdict", integrity["verdict"]),
        ])
    breakable_fields = {
        "Source", "Additional sources", "Transitive definitions", "Prerequisites",
        "Consumers", "Owned Lean file", "Exact imports", "Signature manifest",
        "Scoped validation",
    }
    rendered_fields = []
    for name, value in fields:
        if name == "Lean plan":
            rendered = value
        elif name in breakable_fields:
            rendered = tex_breakable(str(value))
        else:
            rendered = tex_escape(str(value))
        rendered_fields.append(f"\\BlueprintField{{{name}}}{{{rendered}}}")
    body = "\n".join(rendered_fields)
    # Contract/integrity entries are deliberately detailed; keep each fixed
    # minipage within one page while preserving all machine-visible fields.
    compact = bool(node.get("implementation_contract") or node.get("integrity"))
    prefix = (r"\begingroup\fontsize{8}{8.5}\selectfont"
              r"\setlength{\itemsep}{0pt}\setlength{\parsep}{0pt}"
              r"\setlength{\topsep}{0pt}\setlength{\partopsep}{0pt}") if compact else ""
    suffix = r"\endgroup" if compact else ""
    return (f"\\begin{{BlueprintNode}}{{{tex_escape(node['id'])}}}{{{tex_escape(node['title'])}}}\n"
            f"{prefix}\n{body}\n{suffix}\n\\end{{BlueprintNode}}\n")


def outputs(nodes_doc: dict[str, Any], gaps_doc: dict[str, Any],
            externals_doc: dict[str, Any]) -> dict[Path, str]:
    graph = graph_document(nodes_doc)
    rendered_nodes = {node["id"]: node for node in graph["nodes"]}
    result: dict[Path, str] = {ROOT / "generated/graph.json": canonical_json(graph)}
    dot = ["digraph QPBT {", "  rankdir=LR;", "  node [shape=box, fontsize=9];"]
    for node in sorted(nodes_doc["nodes"], key=lambda n: n["id"]):
        color = {"exact": "#d9ead3", "faithful-boundary": "#cfe2f3",
                 "repaired-internal": "#fce5cd", "external-boundary": "#ead1dc"}[node["fidelity"]]
        dot.append(f'  "{node["id"]}" [label="{node["id"]}\\n{node["title"]}", style=filled, fillcolor="{color}"];')
    for node in sorted(nodes_doc["nodes"], key=lambda n: n["id"]):
        for dep in sorted(node["prerequisites"]):
            dot.append(f'  "{dep}" -> "{node["id"]}";')
    dot.append("}")
    result[ROOT / "generated/graph.dot"] = "\n".join(dot) + "\n"
    for chapter in CHAPTERS:
        entries = [rendered_nodes[node["id"]] for node in nodes_doc["nodes"]
                   if node["chapter"] == chapter]
        text = "% Generated by blueprint/check.py. Do not edit.\n"
        text += "\n".join(render_entry(node, node["consumers"]) for node in entries)
        result[ROOT / f"src/generated/chapter-{chapter}-entries.tex"] = text
    gaps = ["% Generated by blueprint/check.py. Do not edit.",
            r"\begin{longtable}{p{0.06\linewidth}p{0.16\linewidth}p{0.31\linewidth}p{0.35\linewidth}}",
            r"\textbf{ID} & \textbf{Class/source} & \textbf{Disposition} & \textbf{Public effect} \\",
            r"\hline"]
    for gap in gaps_doc["gaps"]:
        breakable_source = " ".join(
            f"\\seqsplit{{{tex_escape(part)}}}" for part in gap["source"].split()
        )
        class_and_source = f"{tex_escape(gap['class'])}; {breakable_source}"
        fields = [tex_escape(gap["id"]), class_and_source,
                  tex_escape(gap["disposition"]), tex_escape(gap["public_effect"])]
        gaps.append(" & ".join(fields) + r" \\")
    gaps.extend([r"\end{longtable}", ""])
    result[ROOT / "src/generated/gaps.tex"] = "\n".join(gaps)
    externals = ["% Generated by blueprint/check.py. Do not edit.",
                 r"\begin{longtable}{p{0.12\linewidth}p{0.13\linewidth}p{0.3\linewidth}p{0.33\linewidth}}",
                 r"\textbf{ID} & \textbf{Pin} & \textbf{Role} & \textbf{Treatment} \\",
                 r"\hline"]
    for source in externals_doc["sources"]:
        fields = [source["id"], source["arxiv"], source["role"], source["treatment"]]
        externals.append(" & ".join(tex_escape(field) for field in fields) + r" \\")
    externals.extend([r"\end{longtable}", ""])
    result[ROOT / "src/generated/external-sources.tex"] = "\n".join(externals)
    return result


def scan_for_false_links() -> list[str]:
    errors: list[str] = []
    forbidden = ("\\lean{", "\\leanok")
    for path in sorted((ROOT / "src").rglob("*.tex")):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            if token in text:
                errors.append(f"{path.relative_to(ROOT)}: forbidden nonexistent-declaration claim {token}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    parser.add_argument("--source-root", type=Path)
    args = parser.parse_args()
    nodes_doc = load_json(ROOT / "metadata/nodes.json")
    gaps_doc = load_json(ROOT / "metadata/gaps.json")
    externals_doc = load_json(ROOT / "metadata/external-sources.json")
    errors = validate_data(nodes_doc, gaps_doc, externals_doc) + scan_for_false_links()
    if args.source_root:
        errors.extend(validate_sources(nodes_doc, args.source_root.resolve()))
    expected = outputs(nodes_doc, gaps_doc, externals_doc)
    if args.write and not errors:
        for path, text in expected.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8", newline="\n")
    if args.check:
        for path, text in expected.items():
            if not path.is_file() or path.read_text(encoding="utf-8") != text:
                errors.append(f"stale or missing generated output: {path.relative_to(ROOT)}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"OK: {len(nodes_doc['nodes'])} nodes, 12 chapters, acyclic graph, deterministic outputs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
