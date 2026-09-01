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
SIGNATURE_MANIFEST_KEYS = {"path", "begin_marker", "end_marker", "sha256"}
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
        "F06-CL", "F07-TYPED", "F08-MAGIC-GAME", "F09-LDT-GAME",
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
    "sorry_count": 2,
    "sorry_declarations": [
        "MIPStarRE.QPBT.fieldDataOfOddExponent",
        "MIPStarRE.QPBT.pauliSoundness",
    ],
    "sorry_reasons": {
        "MIPStarRE.QPBT.fieldDataOfOddExponent": "G16",
        "MIPStarRE.QPBT.pauliSoundness": "main-theorem",
    },
    "proof_complete_sorry_count": 0,
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


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
    if contract["writer_lane"] not in {"field", "approximation"}:
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
        foreign = set(allowed_sorries) - set(node["lean"]["names"])
        if foreign:
            errors.append(f"{node_id}: implementation permits foreign sorries {sorted(foreign)}")
    if contract["proof_complete_sorry_count"] != 0:
        errors.append(f"{node_id}: proof-complete implementation must permit zero sorries")
    return errors


def validate_data(nodes_doc: dict[str, Any], gaps_doc: dict[str, Any],
                  externals_doc: dict[str, Any]) -> list[str]:
    errors: list[str] = []
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
