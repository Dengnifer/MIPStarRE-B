"""Adversarial tests for the deterministic QPBT blueprint checker."""

from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("blueprint_check", ROOT / "check.py")
assert SPEC and SPEC.loader
check = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check)
PDF_SPEC = importlib.util.spec_from_file_location("blueprint_check_pdf", ROOT / "check_pdf.py")
assert PDF_SPEC and PDF_SPEC.loader
check_pdf = importlib.util.module_from_spec(PDF_SPEC)
PDF_SPEC.loader.exec_module(check_pdf)


def load(name: str):
    return json.loads((ROOT / "metadata" / name).read_text(encoding="utf-8"))


class BlueprintCheckTests(unittest.TestCase):
    def setUp(self) -> None:
        self.nodes = load("nodes.json")
        self.gaps = load("gaps.json")
        self.externals = load("external-sources.json")

    def errors(self, nodes=None, gaps=None, externals=None):
        return check.validate_data(
            nodes or self.nodes, gaps or self.gaps, externals or self.externals
        )

    def test_canonical_metadata_is_valid_and_every_target_reachable(self) -> None:
        self.assertEqual([], self.errors())
        graph = check.graph_document(self.nodes)
        self.assertEqual(len(self.nodes["nodes"]), len(graph["topological_order"]))
        for target in self.nodes["targets"].values():
            self.assertIn(target, graph["topological_order"])

    def test_every_target_name_and_contract_is_validated(self) -> None:
        for target_name in sorted(check.TARGET_KEYS):
            with self.subTest(target=target_name):
                bad = copy.deepcopy(self.nodes)
                bad["targets"][target_name] = "NOT-A-NODE"
                self.assertTrue(any(
                    f"targets.{target_name} must name an existing node" in error
                    for error in self.errors(nodes=bad)
                ))

        missing_key = copy.deepcopy(self.nodes)
        del missing_key["targets"]["binary"]
        self.assertTrue(any("targets must use the exact keys" in error
                            for error in self.errors(nodes=missing_key)))

        missing_contract = copy.deepcopy(self.nodes)
        del missing_contract["required_target_spines"]["completeness"]
        self.assertTrue(any("required_target_spines must use the exact keys" in error
                            for error in self.errors(nodes=missing_contract)))

        weakened_contract = copy.deepcopy(self.nodes)
        weakened_contract["required_target_spines"]["canonical_complexity"].remove(
            "K03B-LOW-DEGREE-COMPLEXITY"
        )
        self.assertTrue(any("canonical reachability contract" in error
                            for error in self.errors(nodes=weakened_contract)))

    def test_binary_and_complexity_targets_cannot_be_detached(self) -> None:
        cases = (
            ("B01-BINARY", "F10-PAULI-BINARY", "binary"),
            ("K04-GAME-COMPLEXITY", None, "canonical_complexity"),
        )
        for node_id, removed_dependency, target_name in cases:
            with self.subTest(node=node_id):
                bad = copy.deepcopy(self.nodes)
                node = next(node for node in bad["nodes"] if node["id"] == node_id)
                node["prerequisites"] = (
                    [] if removed_dependency is None else
                    [dep for dep in node["prerequisites"] if dep != removed_dependency]
                )
                by_id = {item["id"]: item for item in bad["nodes"]}
                prerequisites = {item["id"]: set(item["prerequisites"])
                                 for item in bad["nodes"]}
                node["transitive_definitions"] = check.definition_ancestor_ids(
                    node_id, by_id, prerequisites
                )
                self.assertTrue(any(
                    f"{target_name} target misses required spine" in error
                    for error in self.errors(nodes=bad)
                ))

    def test_stage_4a_skeleton_proof_debt_is_exact(self) -> None:
        expected = {
            "stage": "minimal",
            "sorry_count": 4,
            "sorry_declarations": [
                "MIPStarRE.QPBT.fieldDataOfOddExponent",
                "MIPStarRE.QPBT.ExecutableCLSampler.downsizeCompiler_exists",
                "MIPStarRE.QPBT.ExecutableCLSampler.downsize_time",
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
        self.assertEqual(expected, self.nodes["skeleton_plan"])
        for mutation in (
            {**expected, "stage": "complete"},
            {**expected, "sorry_count": 3},
            {**expected, "sorry_declarations": ["MIPStarRE.QPBT.helper"]},
            {**expected, "sorry_reasons": {
                "MIPStarRE.QPBT.fieldDataOfOddExponent": "untracked",
                "MIPStarRE.QPBT.pauliSoundness": "main-theorem",
            }},
            {**expected, "proof_complete_sorry_count": 1},
        ):
            with self.subTest(mutation=mutation):
                bad = copy.deepcopy(self.nodes)
                bad["skeleton_plan"] = mutation
                self.assertTrue(any("exact minimal-skeleton proof debt" in error
                                    for error in self.errors(nodes=bad)))

    def test_executable_cl_stage_4a_debt_is_exact_and_private_helper_stays_private(
            self) -> None:
        node = next(item for item in self.nodes["nodes"]
                    if item["id"] == check.EXECUTABLE_CL_OWNER_ID)
        public_names = node["lean"]["names"]
        allowed = node["implementation_contract"]["allowed_minimal_sorries"]

        self.assertEqual(check.EXECUTABLE_CL_STAGE_4A_SORRIES, allowed)
        self.assertEqual(56, len(public_names))
        self.assertNotIn(
            "MIPStarRE.QPBT.ExecutableCLSampler.downsizeCompiler_exists",
            public_names,
        )
        for proved_declaration in (
            "MIPStarRE.QPBT.ExecutableCLSampler.downsize",
            "MIPStarRE.QPBT.ExecutableCLSampler.downsize_dimension",
            "MIPStarRE.QPBT.ExecutableCLSampler.downsize_associated",
            "MIPStarRE.QPBT.ExecutableCLSampler.sample_downsize",
        ):
            self.assertNotIn(proved_declaration, allowed)

        mutations = (
            [],
            ["MIPStarRE.QPBT.ExecutableCLSampler.downsize_time"],
            [
                "MIPStarRE.QPBT.ExecutableCLSampler.downsizeCompiler_exists",
                "MIPStarRE.QPBT.ExecutableCLSampler.downsize_dimension",
            ],
            [
                *check.EXECUTABLE_CL_STAGE_4A_SORRIES,
                "MIPStarRE.QPBT.ExecutableCLSampler.sample_downsize",
            ],
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                bad = copy.deepcopy(self.nodes)
                target = next(item for item in bad["nodes"]
                              if item["id"] == check.EXECUTABLE_CL_OWNER_ID)
                target["implementation_contract"]["allowed_minimal_sorries"] = mutation
                self.assertTrue(any(
                    "implementation contract must remain exact" in error
                    for error in self.errors(nodes=bad)
                ))

        exposed = copy.deepcopy(self.nodes)
        target = next(item for item in exposed["nodes"]
                      if item["id"] == check.EXECUTABLE_CL_OWNER_ID)
        target["lean"]["names"].append(
            "MIPStarRE.QPBT.ExecutableCLSampler.downsizeCompiler_exists"
        )
        self.assertTrue(any(
            "executable CL callable names must remain exact" in error
            for error in self.errors(nodes=exposed)
        ))

    def test_duplicate_ids_and_lean_names_are_rejected(self) -> None:
        bad = copy.deepcopy(self.nodes)
        bad["nodes"][1]["id"] = bad["nodes"][0]["id"]
        bad["nodes"][1]["lean"]["names"] = bad["nodes"][0]["lean"]["names"]
        errors = self.errors(nodes=bad)
        self.assertTrue(any("duplicate node id" in error for error in errors))
        self.assertTrue(any("duplicate planned Lean declaration" in error for error in errors))

    def test_cycle_is_rejected(self) -> None:
        bad = copy.deepcopy(self.nodes)
        first = bad["nodes"][0]
        second = bad["nodes"][1]
        first["prerequisites"] = [second["id"]]
        second["prerequisites"] = [first["id"]]
        self.assertTrue(any("dependency cycle" in error for error in self.errors(nodes=bad)))

    def test_unknown_edge_and_missing_soundness_spine_are_rejected(self) -> None:
        bad = copy.deepcopy(self.nodes)
        soundness = next(node for node in bad["nodes"] if node["id"] == "S01-SOUNDNESS")
        soundness["prerequisites"] = []
        bad["nodes"][0]["prerequisites"] = ["NOT-A-NODE"]
        errors = self.errors(nodes=bad)
        self.assertTrue(any("unknown prerequisites" in error for error in errors))
        self.assertTrue(any("misses required spine" in error for error in errors))

    def test_repaired_node_requires_gap_and_reciprocal_link(self) -> None:
        bad = copy.deepcopy(self.nodes)
        repaired = next(node for node in bad["nodes"] if node["id"] == "A01-INDICATOR")
        repaired["gap_ids"] = []
        errors = self.errors(nodes=bad)
        self.assertTrue(any("repaired internal node must cite a gap" in error for error in errors))
        self.assertTrue(any("missing reciprocal link" in error for error in errors))

    def test_external_pin_must_include_exact_version(self) -> None:
        bad = copy.deepcopy(self.externals)
        bad["sources"][0]["arxiv"] = "1904.05870"
        self.assertTrue(any("arXiv version is not exact" in error
                            for error in self.errors(externals=bad)))

    def test_external_pin_contract_fields_must_agree(self) -> None:
        bad = copy.deepcopy(self.externals)
        tensor = next(source for source in bad["sources"] if source["id"] == "EXT-TENSOR")
        tensor["version"] = "v2"
        tensor["pin_contract"]["source_url"] = "https://arxiv.org/src/2111.08131v2"
        errors = self.errors(externals=bad)
        self.assertTrue(any("version disagrees" in error for error in errors))
        self.assertTrue(any("pin contract disagrees" in error for error in errors))

        missing = copy.deepcopy(self.externals)
        tensor = next(source for source in missing["sources"] if source["id"] == "EXT-TENSOR")
        del tensor["pin_contract"]
        self.assertTrue(any("published pin requires a pin contract" in error
                            for error in self.errors(externals=missing)))

    def test_tensor_external_contract_is_immutable(self) -> None:
        for version in ("v2", "v4"):
            with self.subTest(version=version):
                bad = copy.deepcopy(self.externals)
                tensor = next(source for source in bad["sources"]
                              if source["id"] == "EXT-TENSOR")
                arxiv = f"2111.08131{version}"
                tensor.update({
                    "arxiv": arxiv,
                    "version": version,
                    "url": f"https://arxiv.org/abs/{arxiv}",
                })
                tensor["pin_contract"].update({
                    "versioned_id": arxiv,
                    "metadata_url": f"https://arxiv.org/abs/{arxiv}",
                    "source_url": f"https://arxiv.org/src/{arxiv}",
                })
                self.assertTrue(any("authoritative contract must remain exact" in error
                                    for error in self.errors(externals=bad)))

        mutations = {
            "generic status": ("status", "pinned"),
            "authority": ("pin_contract.authority", "publisher mirror"),
            "last revised": ("pin_contract.last_revised", "2022-12-07"),
            "release": ("pin_contract.release", "draft"),
            "verification": ("pin_contract.verification_basis", "unverified"),
        }
        for name, (path, value) in mutations.items():
            with self.subTest(name=name):
                bad = copy.deepcopy(self.externals)
                tensor = next(source for source in bad["sources"]
                              if source["id"] == "EXT-TENSOR")
                if path.startswith("pin_contract."):
                    tensor["pin_contract"][path.removeprefix("pin_contract.")] = value
                else:
                    tensor[path] = value
                self.assertTrue(any("authoritative contract must remain exact" in error
                                    for error in self.errors(externals=bad)))

        downgraded = copy.deepcopy(self.externals)
        tensor = next(source for source in downgraded["sources"]
                      if source["id"] == "EXT-TENSOR")
        tensor["status"] = "pinned"
        del tensor["pin_contract"]
        self.assertTrue(any("authoritative contract must remain exact" in error
                            for error in self.errors(externals=downgraded)))

        renamed = copy.deepcopy(self.externals)
        next(source for source in renamed["sources"]
             if source["id"] == "EXT-TENSOR")["id"] = "EXT-TENSOR-RENAMED"
        self.assertTrue(any("authoritative external source missing: EXT-TENSOR" in error
                            for error in self.errors(externals=renamed)))

    def test_unresolved_soundness_external_is_rejected(self) -> None:
        bad = copy.deepcopy(self.externals)
        tensor = next(source for source in bad["sources"] if source["id"] == "EXT-TENSOR")
        tensor["status"] = "provisional-until-review"
        self.assertTrue(any("soundness-critical external source EXT-TENSOR is unresolved" in error
                            for error in self.errors(externals=bad)))

    def test_transitive_definitions_are_exact_definition_ancestor_closure(self) -> None:
        soundness = next(node for node in self.nodes["nodes"] if node["id"] == "S01-SOUNDNESS")
        by_id = {node["id"]: node for node in self.nodes["nodes"]}
        self.assertTrue(soundness["transitive_definitions"])
        self.assertTrue(all(by_id[node_id]["kind"] == "definition"
                            for node_id in soundness["transitive_definitions"]))

        missing = copy.deepcopy(self.nodes)
        next(node for node in missing["nodes"]
             if node["id"] == "S01-SOUNDNESS")["transitive_definitions"].pop()
        self.assertTrue(any("definition-ancestor closure" in error
                            for error in self.errors(nodes=missing)))

        theorem_injected = copy.deepcopy(self.nodes)
        next(node for node in theorem_injected["nodes"]
             if node["id"] == "R05-ROBUSTNESS")["transitive_definitions"].append(
                 "A15-UNITARY"
             )
        self.assertTrue(any("definition-ancestor closure" in error
                            for error in self.errors(nodes=theorem_injected)))

    def test_graph_derives_transitive_definitions(self) -> None:
        graph = check.graph_document(self.nodes)
        soundness = next(node for node in graph["nodes"] if node["id"] == "S01-SOUNDNESS")
        prerequisites = {node["id"]: set(node["prerequisites"])
                         for node in self.nodes["nodes"]}
        by_id = {node["id"]: node for node in self.nodes["nodes"]}
        expected = check.definition_ancestor_ids("S01-SOUNDNESS", by_id, prerequisites)
        self.assertEqual(expected, soundness["transitive_definitions"])

    def test_source_faithful_magic_square_edges(self) -> None:
        by_id = {node["id"]: node for node in self.nodes["nodes"]}
        prerequisites = {node_id: set(node["prerequisites"])
                         for node_id, node in by_id.items()}

        self.assertEqual(
            {"F04-CONSISTENCY"},
            prerequisites["E01-ORTHO"],
        )
        self.assertEqual({"G02-GAME"}, prerequisites["G03-COMPLETENESS"])
        completeness_ancestors = check.dependency_ancestors(
            "G03-COMPLETENESS", prerequisites
        )
        self.assertIn("F08-MAGIC-GAME", completeness_ancestors)
        self.assertNotIn("E02-MAGIC-SQUARE", completeness_ancestors)

    def test_paper_index_repairs_and_complexity_anchors_are_explicit(self) -> None:
        by_id = {node["id"]: node for node in self.nodes["nodes"]}

        binary_conversion = by_id["F10-PAULI-BINARY"]
        self.assertIn("every natural tensor length L", binary_conversion["statement"])
        self.assertIn("j ranges through k, not q", binary_conversion["encoding"])
        self.assertIn("a_j", binary_conversion["encoding"])
        self.assertIn("G14", binary_conversion["gap_ids"])
        self.assertIn("G14", by_id["B01-BINARY"]["gap_ids"])

        observables = by_id["A04-WIN-OBS"]
        self.assertIn("r_X/r_Z", observables["encoding"])
        self.assertIn("G15", observables["gap_ids"])

        canonical = by_id["K03-INTRO-COMPLEXITY"]
        self.assertIn("integer tuple (q,m,d)", canonical["statement"])
        self.assertNotIn("finite-field representation", canonical["statement"])

        complexity = by_id["K04-GAME-COMPLEXITY"]
        for dependency in ("K03A-FIELD-ARITHMETIC", "K03B-LOW-DEGREE-COMPLEXITY"):
            self.assertIn(dependency, complexity["prerequisites"])
        self.assertIn("exactly the three displayed complexity items", complexity["encoding"])
        self.assertNotIn("sampler", complexity["statement"].lower())
        self.assertNotIn("question/answer", complexity["statement"].lower())

    def test_direct_sum_detyping_and_finiteness_contracts_are_exact(self) -> None:
        by_id = {node["id"]: node for node in self.nodes["nodes"]}

        f06 = by_id["F06-CL"]
        self.assertIn("MIPStarRE.QPBT.CLSampler.sample_directSum", f06["lean"]["names"])
        self.assertEqual(check.F06_SOURCE_ANCHOR, f06["source"])
        self.assertEqual("faithful-boundary", f06["fidelity"])
        self.assertEqual("faithful boundary", f06["integrity"]["verdict"])
        for term in check.F06_EXECUTABLE_OWNER_TERMS:
            self.assertIn(term, f06["boundary_hypotheses"].lower())

        executable_cl = by_id[check.EXECUTABLE_CL_OWNER_ID]
        self.assertEqual(
            check.EXECUTABLE_CL_SOURCE_ANCHORS,
            [executable_cl["source"], *executable_cl["additional_sources"]],
        )
        self.assertEqual(check.EXECUTABLE_CL_PREREQUISITES,
                         executable_cl["prerequisites"])
        self.assertEqual(check.EXECUTABLE_CL_LEAN_NAMES,
                         executable_cl["lean"]["names"])
        self.assertEqual(check.EXECUTABLE_CL_IMPLEMENTATION_CONTRACT,
                         executable_cl["implementation_contract"])
        self.assertEqual(check.EXECUTABLE_CL_CONTRACT,
                         check.executable_cl_contract(executable_cl))

        f07 = by_id["F07-TYPED"]
        self.assertEqual(check.TYPED_SOURCE_ANCHOR, f07["source"])
        self.assertEqual(check.TYPED_PREREQUISITES, f07["prerequisites"])
        self.assertEqual(check.TYPED_LEAN_NAMES, f07["lean"]["names"])
        self.assertEqual(check.F07_FINITENESS_CONTRACT,
                         check.f07_finiteness_contract(f07))
        self.assertIn(
            "Among question/answer content fibers, only the sampler carrier is asserted finite.",
            f07["statement"],
        )

        game_semantics = by_id[check.GAME_SEMANTICS_OWNER_ID]
        self.assertEqual(
            check.GAME_SEMANTICS_SOURCE_ANCHORS,
            [game_semantics["source"], *game_semantics["additional_sources"]],
        )
        self.assertEqual(check.GAME_SEMANTICS_PREREQUISITES,
                         game_semantics["prerequisites"])
        self.assertEqual(check.GAME_SEMANTICS_LEAN_NAMES,
                         game_semantics["lean"]["names"])

        detyping = by_id[check.DETYPING_OWNER_ID]
        self.assertEqual(check.DETYPING_SOURCE_ANCHOR, detyping["source"])
        self.assertEqual(check.DETYPING_PREREQUISITES, detyping["prerequisites"])
        self.assertEqual(check.DETYPING_LEAN_NAMES, detyping["lean"]["names"])
        self.assertFalse(any(dependency.startswith(("K03", "K04"))
                             for dependency in detyping["prerequisites"]))
        for term in check.F07A_EXECUTABLE_OWNER_TERMS:
            self.assertIn(term, detyping["boundary_hypotheses"].lower())
        self.assertEqual(check.F07A_LEAN_ASSUMPTIONS,
                         detyping["integrity"]["lean_assumptions"])

        for node_id, contract in check.NON_DETYPING_COMPLEXITY_CONTRACTS.items():
            node = by_id[node_id]
            self.assertEqual(contract["generated_lines"],
                             node["source"]["generated_lines"])
            self.assertEqual(contract["lean_names"], node["lean"]["names"])
            ownership_text = " ".join(
                str(node[field]) for field in
                ("statement", "encoding", "boundary_hypotheses")
            ).lower()
            self.assertNotIn("detyp", ownership_text)

        for mutation, phrase in (
            ("missing_theorem", "direct-sum product-distribution theorem"),
            ("missing_game_owner", "missing exact game-semantics owner"),
            ("wrong_game_source", "game-semantics source ranges must remain exact"),
            ("wrong_game_dependencies", "game-semantics prerequisites must remain exact"),
            ("wrong_game_names", "game-semantics callable names must remain exact"),
            ("wrong_typed_source", "typed source range must remain exact"),
            ("wrong_typed_names", "typed callable names must remain exact"),
            ("missing_owner", "missing exact detyping owner"),
            ("wrong_source", "detyping source range must remain exact"),
            ("wrong_dependencies", "detyping prerequisites must remain exact"),
            ("wrong_names", "detyping callable names must remain exact"),
            ("finite_fibers", "generic dependent-fiber finiteness contract must remain exact"),
            ("k03_detyping", "must not own detyping"),
            ("k04_names", "non-detyping callable ownership must remain exact"),
        ):
            with self.subTest(mutation=mutation):
                bad = copy.deepcopy(self.nodes)
                bad_by_id = {node["id"]: node for node in bad["nodes"]}
                if mutation == "missing_theorem":
                    bad_by_id["F06-CL"]["lean"]["names"].remove(
                        "MIPStarRE.QPBT.CLSampler.sample_directSum"
                    )
                elif mutation == "missing_game_owner":
                    bad["nodes"].remove(bad_by_id[check.GAME_SEMANTICS_OWNER_ID])
                elif mutation == "wrong_game_source":
                    bad_by_id[check.GAME_SEMANTICS_OWNER_ID][
                        "additional_sources"
                    ][1]["generated_lines"] = [127, 190]
                elif mutation == "wrong_game_dependencies":
                    bad_by_id[check.GAME_SEMANTICS_OWNER_ID]["prerequisites"] = [
                        "F04-DISTANCE"
                    ]
                elif mutation == "wrong_game_names":
                    bad_by_id[check.GAME_SEMANTICS_OWNER_ID]["lean"]["names"].pop()
                elif mutation == "wrong_typed_source":
                    bad_by_id["F07-TYPED"]["source"]["generated_lines"] = [57, 194]
                elif mutation == "wrong_typed_names":
                    bad_by_id["F07-TYPED"]["lean"]["names"].remove(
                        "MIPStarRE.QPBT.TypedSampler.sample_downsize"
                    )
                elif mutation == "missing_owner":
                    bad["nodes"].remove(bad_by_id[check.DETYPING_OWNER_ID])
                elif mutation == "wrong_source":
                    bad_by_id[check.DETYPING_OWNER_ID]["source"]["generated_lines"] = [360, 579]
                elif mutation == "wrong_dependencies":
                    bad_by_id[check.DETYPING_OWNER_ID]["prerequisites"] = ["F07-TYPED"]
                elif mutation == "wrong_names":
                    bad_by_id[check.DETYPING_OWNER_ID]["lean"]["names"].pop()
                elif mutation == "k03_detyping":
                    bad_by_id["K03-INTRO-COMPLEXITY"]["statement"] += (
                        " It also owns detyping."
                    )
                elif mutation == "k04_names":
                    bad_by_id["K04-GAME-COMPLEXITY"]["lean"]["names"] = [
                        "MIPStarRE.QPBT.detyping_complexity"
                    ]
                else:
                    bad_by_id["F07-TYPED"]["boundary_hypotheses"] += " Finite dependent fibers."
                self.assertTrue(any(phrase in error for error in self.errors(nodes=bad)))

    def test_executable_cl_contract_is_fail_closed_and_adversarial(self) -> None:
        cases = (
            ("missing_owner", "missing exact executable CL owner"),
            ("wrong_source", "executable CL source anchors must remain exact"),
            ("wrong_dependencies", "executable CL prerequisites must remain exact"),
            ("wrong_module", "executable CL module must remain exact"),
            ("wrong_names", "executable CL callable names must remain exact"),
            ("wrong_import", "implementation contract must remain exact"),
            ("wrong_manifest", "implementation contract must remain exact"),
            ("wrong_kind", "node kind and fidelity must remain exact"),
            ("six_modes", "executable CL semantic contract must remain exact"),
            ("opaque_runtime", "executable CL semantic contract must remain exact"),
            ("obligation_input", "executable CL semantic contract must remain exact"),
            ("fabricated_machine", "executable CL semantic contract must remain exact"),
            ("wrong_dimension", "executable CL semantic contract must remain exact"),
        )
        for mutation, phrase in cases:
            with self.subTest(mutation=mutation):
                bad = copy.deepcopy(self.nodes)
                by_id = {node["id"]: node for node in bad["nodes"]}
                node = by_id[check.EXECUTABLE_CL_OWNER_ID]
                if mutation == "missing_owner":
                    bad["nodes"].remove(node)
                elif mutation == "wrong_source":
                    node["additional_sources"][2]["generated_lines"] = [662, 711]
                elif mutation == "wrong_dependencies":
                    node["prerequisites"] = []
                elif mutation == "wrong_module":
                    node["lean"]["module"] = "MIPStarRE.QPBT.Game.Detyping"
                elif mutation == "wrong_names":
                    node["lean"]["names"].remove(
                        "MIPStarRE.QPBT.ExecutableCLSampler.downsize_time"
                    )
                elif mutation == "wrong_import":
                    node["implementation_contract"]["imports"].remove(
                        "Mathlib.Computability.TuringMachine.Computable"
                    )
                elif mutation == "wrong_manifest":
                    node["implementation_contract"]["signature_manifest"]["sha256"] = (
                        "0" * 64
                    )
                elif mutation == "wrong_kind":
                    node["kind"] = "lemma"
                elif mutation == "six_modes":
                    node["statement"] = node["statement"].replace(
                        "distinct dimension, marginal, linear, and factor query modes",
                        "six query modes",
                    )
                elif mutation == "opaque_runtime":
                    node["integrity"]["lean_conclusion"] = (
                        "An unspecified executable runtime contract."
                    )
                elif mutation == "obligation_input":
                    node["boundary_hypotheses"] += (
                        " A caller may supply any missing correctness obligation."
                    )
                elif mutation == "fabricated_machine":
                    node["encoding"] = node["encoding"].replace(
                        "packSixTapes first fixes tape order with List.ofFn, expands false "
                        "as 01 and true as 10, and appends the 00 terminator after each of "
                        "the six tapes. It is an injective, linear, self-delimiting "
                        "encoding of exact length 2 * (sum tape lengths + 6).",
                        "an axiomatized one-tape machine.",
                    )
                else:
                    node["integrity"]["paper_conclusion"] = (
                        node["integrity"]["paper_conclusion"].replace(
                            "dimension s(n) log q(n)", "dimension s(n) + log q(n)"
                        )
                    )
                self.assertTrue(any(
                    phrase in error for error in self.errors(nodes=bad)
                ))

    def test_executable_cl_source_fidelity_repairs_are_fail_closed(self) -> None:
        node_id = check.EXECUTABLE_CL_OWNER_ID
        by_id = {node["id"]: node for node in self.nodes["nodes"]}
        node = by_id[node_id]
        self.assertIn("0 < n", node["integrity"]["lean_assumptions"])
        self.assertIn("1 <= level", node["integrity"]["lean_conclusion"])
        self.assertIn("RuntimeBigO", node["integrity"]["lean_conclusion"])
        self.assertIn("valid-query finite maximum", node["boundary_hypotheses"])
        self.assertIn("canonical blank normalization", node["boundary_hypotheses"])
        self.assertIn("does not claim the paper's stronger arbitrary unused-payload invariance",
                      node["boundary_hypotheses"])
        self.assertIn("concrete FieldExponentProgram", node["boundary_hypotheses"])
        self.assertIn("field-exponent execution", node["boundary_hypotheses"])
        self.assertIn("linear dual-rail, 00-terminated representation",
                      node["boundary_hypotheses"])
        self.assertIn("expands false as 01 and true as 10", node["encoding"])
        self.assertIn("appends the 00 terminator after each of the six tapes",
                      node["encoding"])
        self.assertIn("exact length 2 * (sum tape lengths + 6)", node["encoding"])
        self.assertIn("CLPrefix/CLFactorInput domains",
                      node["integrity"]["lean_assumptions"])
        self.assertIn("exact PMF.map pushforward", node["integrity"]["lean_conclusion"])

        mutations = (
            ("statement", "positive-index", "all-index"),
            ("encoding", "canonical field codec", "arbitrary caller codec"),
            ("encoding", "dependent valid u/y subtypes", "untyped strings"),
            ("encoding", "expands false as 01 and true as 10", "uses an opaque codec"),
            ("encoding", "00 terminator after each of the six tapes", "one final terminator"),
            ("encoding", "exact length 2 * (sum tape lengths + 6)", "unspecified length"),
            ("boundary_hypotheses", "valid-query finite maximum", "upper-bound field"),
            ("boundary_hypotheses", "canonical blank normalization",
             "arbitrary raw-payload invariance"),
            ("boundary_hypotheses", "concrete FieldExponentProgram",
             "arbitrary exponent function"),
            ("boundary_hypotheses", "field-exponent execution",
             "uncharged metadata"),
            ("integrity.lean_conclusion", "RuntimeBigO", "IsBigO Filter.atTop"),
            ("integrity.lean_conclusion", "exact PMF.map pushforward", "asymptotic law"),
        )
        for field, old, new in mutations:
            with self.subTest(field=field, old=old):
                bad = copy.deepcopy(self.nodes)
                target = next(item for item in bad["nodes"] if item["id"] == node_id)
                container = target
                key = field
                if "." in field:
                    parent, key = field.split(".", 1)
                    container = target[parent]
                self.assertIn(old, container[key])
                container[key] = container[key].replace(old, new, 1)
                self.assertTrue(any(
                    "executable CL semantic contract must remain exact" in error
                    for error in self.errors(nodes=bad)
                ))

        for name in (
            "MIPStarRE.QPBT.RuntimeBigO",
            "MIPStarRE.QPBT.CLQueryDecomposition",
            "MIPStarRE.QPBT.CLSamplerQuery.canonicalTapes",
            "MIPStarRE.QPBT.FieldExponentProgram",
            "MIPStarRE.QPBT.ExecutableCLSampler.fieldProgram",
            "MIPStarRE.QPBT.ExecutableCLSampler.queryTime_eq_validQueryMax",
            "MIPStarRE.QPBT.ExecutableCLSampler.time_eq_max",
            "MIPStarRE.QPBT.ExecutableCLSampler.sample_downsize",
        ):
            with self.subTest(name=name):
                bad = copy.deepcopy(self.nodes)
                target = next(item for item in bad["nodes"] if item["id"] == node_id)
                target["lean"]["names"].remove(name)
                self.assertTrue(any(
                    "executable CL callable names must remain exact" in error
                    for error in self.errors(nodes=bad)
                ))

        no_asymptotics = copy.deepcopy(self.nodes)
        executable = next(item for item in no_asymptotics["nodes"] if item["id"] == node_id)
        executable["implementation_contract"]["imports"].append(
            "Mathlib.Analysis.Asymptotics.Defs"
        )
        self.assertTrue(any(
            "implementation contract must remain exact" in error
            for error in self.errors(nodes=no_asymptotics)
        ))

    def test_executable_cl_exponent_gap_is_reciprocal_and_issue_bound(self) -> None:
        node_id = check.EXECUTABLE_CL_OWNER_ID
        node = next(item for item in self.nodes["nodes"] if item["id"] == node_id)
        gap = next(item for item in self.gaps["gaps"] if item["id"] == "G19")

        self.assertEqual(["G19"], node["gap_ids"])
        self.assertEqual([node_id], gap["affected_nodes"])
        self.assertEqual("QPBT-054", gap["issue"])
        self.assertIn("finite-fields.tex:245-247,283-307 [1561-1563,1599-1623]",
                      gap["source"])
        for required in ("arbitrary admissible field-size function", "one downsized Turing machine",
                         "log q(n)", "TIME_S(n)"):
            self.assertIn(required, gap["paper_problem"])
        self.assertIn("concrete intrinsic FieldExponentProgram", gap["disposition"])
        self.assertIn("Do not fabricate or assert an arbitrary admissible-family-to-machine theorem",
                      gap["disposition"])
        self.assertIn("expands TIME_S(n) to charge intrinsic exponent computation",
                      gap["public_effect"])
        self.assertIn("no arbitrary family-to-machine premise or theorem is exposed",
                      gap["public_effect"])

        missing_from_node = copy.deepcopy(self.nodes)
        next(item for item in missing_from_node["nodes"]
             if item["id"] == node_id)["gap_ids"] = []
        self.assertTrue(any(
            "missing reciprocal link" in error
            for error in self.errors(nodes=missing_from_node)
        ))

        missing_from_gap = copy.deepcopy(self.gaps)
        next(item for item in missing_from_gap["gaps"]
             if item["id"] == "G19")["affected_nodes"] = []
        self.assertTrue(any(
            "lacks reciprocal affected-node link" in error
            for error in self.errors(gaps=missing_from_gap)
        ))

    def test_executable_cl_signature_rejects_concrete_a04_defects(self) -> None:
        node = next(item for item in self.nodes["nodes"]
                    if item["id"] == check.EXECUTABLE_CL_OWNER_ID)
        manifest = node["implementation_contract"]["signature_manifest"]
        text = (ROOT.parent / manifest["path"]).read_text(encoding="utf-8")
        block = text.split(manifest["begin_marker"], 1)[1].split(
            manifest["end_marker"], 1
        )[0].strip()
        self.assertEqual([], check.executable_cl_signature_errors(block))
        self.assertEqual(56, len(node["lean"]["names"]))
        self.assertEqual(4, len(node["implementation_contract"]["imports"]))

        for required in (
            "abbrev CLPrefix",
            "Turing.FinTM2",
            "Turing.TM2OutputsInTime",
            "execution.runInTime.toEvalsTo.steps",
            "def CLSamplerQuery.canonicalTapes",
            "structure FieldExponentProgram",
            "fieldProgram : FieldExponentProgram Q",
            "(S.validQueries n hn).sup (S.executedSteps n hn)",
            "Nat.max (S.queryTime n hn) (S.fieldProgram.steps n hn)",
            "(List.ofFn input).flatMap fun tape =>",
            "| false => [false, true]",
            "| true => [true, false]) ++ [false, false]",
        ):
            with self.subTest(missing=required):
                self.assertIn(required, block)
                mutated = block.replace(required, "REMOVED_CONTRACT_TERM")
                self.assertTrue(check.executable_cl_signature_errors(mutated))

        cantor_body = (
            "Computability.encodingNatBool.encode "
            "(Encodable.encode (List.ofFn input))"
        )
        self.assertTrue(any(
            "forbidden pattern" in error
            for error in check.executable_cl_signature_errors(f"{block}\n{cantor_body}")
        ))

        for forbidden in (
            "factor_cover : Prop",
            "validQueryFinset",
            "output : SixTapeInput -> List Bool",
            "run : SixTapeInput -> List Bool -> Nat -> Prop",
            "def CLSamplerQuery.tapes",
            "theorem ExecutableCLSampler.time_eq_validQueryMax",
            "axiom fabricatedRuntime : Prop",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertTrue(check.executable_cl_signature_errors(
                    f"{block}\n{forbidden}"
                ))

    def test_executable_cl_historical_report_is_fail_closed(self) -> None:
        canonical = ROOT.parent / check.EXECUTABLE_CL_HISTORICAL_REPORT_PATH
        report_bytes = canonical.read_bytes()
        self.assertEqual([], check.executable_cl_historical_report_errors(ROOT.parent))

        with tempfile.TemporaryDirectory() as temporary_directory:
            repository_root = Path(temporary_directory)
            historical = repository_root / check.EXECUTABLE_CL_HISTORICAL_REPORT_PATH
            historical.parent.mkdir(parents=True)
            mutated = bytearray(report_bytes)
            mutated[0] ^= 1
            historical.write_bytes(mutated)
            self.assertEqual(
                [check.EXECUTABLE_CL_HISTORICAL_REPORT_HASH_ERROR],
                check.executable_cl_historical_report_errors(repository_root),
            )

    def test_typed_finiteness_and_executable_ownership_wording_is_adversarial(self) -> None:
        finiteness_mutations = (
            ("statement", " Finite typed samplers and deciders are exposed."),
            ("encoding", " All typed question and answer families are finite."),
            ("boundary_hypotheses", " Dependent decider fibers are finite."),
            ("lean_assumptions", " Finite typed questions, answers, and deciders are assumed."),
            ("lean_conclusion", " The generic interfaces remain pointwise finite."),
        )
        for field, phrase in finiteness_mutations:
            with self.subTest(field=field):
                bad = copy.deepcopy(self.nodes)
                f07 = next(node for node in bad["nodes"] if node["id"] == "F07-TYPED")
                target = f07["integrity"] if field.startswith("lean_") else f07
                target[field] += phrase
                self.assertTrue(any(
                    "generic dependent-fiber finiteness contract must remain exact" in error
                    for error in self.errors(nodes=bad)
                ))

        conjoined_with_consumer = copy.deepcopy(self.nodes)
        f07 = next(node for node in conjoined_with_consumer["nodes"]
                   if node["id"] == "F07-TYPED")
        f07["boundary_hypotheses"] = f07["boundary_hypotheses"].replace(
            "required by the mathematical game consumer.",
            "required by the mathematical game consumer while finite typed samplers "
            "and deciders are exposed.",
        )
        self.assertTrue(any(
            "generic dependent-fiber finiteness contract must remain exact" in error
            for error in self.errors(nodes=conjoined_with_consumer)
        ))

        hidden_after_disclaimer = copy.deepcopy(self.nodes)
        f07 = next(node for node in hidden_after_disclaimer["nodes"]
                   if node["id"] == "F07-TYPED")
        f07["boundary_hypotheses"] = f07["boundary_hypotheses"].replace(
            "without pointwise finiteness assumptions.",
            "without pointwise finiteness assumptions but dependent decider fibers "
            "are finite.",
        )
        self.assertTrue(any(
            "generic dependent-fiber finiteness contract must remain exact" in error
            for error in self.errors(nodes=hidden_after_disclaimer)
        ))

        finite_f07a = copy.deepcopy(self.nodes)
        detyping = next(node for node in finite_f07a["nodes"]
                        if node["id"] == check.DETYPING_OWNER_ID)
        detyping["integrity"]["lean_assumptions"] = (
            "F07 finite typed interfaces, F04A game semantics, and a machine model."
        )
        self.assertTrue(any(
            "dependent-fiber assumptions must remain exact" in error
            for error in self.errors(nodes=finite_f07a)
        ))

        wrong_fidelity = copy.deepcopy(self.nodes)
        next(node for node in wrong_fidelity["nodes"]
             if node["id"] == "F06-CL")["fidelity"] = "exact"
        self.assertTrue(any(
            "fidelity must match its faithful-boundary integrity verdict" in error
            for error in self.errors(nodes=wrong_fidelity)
        ))

        false_deferral = copy.deepcopy(self.nodes)
        f06 = next(node for node in false_deferral["nodes"] if node["id"] == "F06-CL")
        f06["boundary_hypotheses"] = (
            "All spaces and randomness are finite. Raw Turing strings, executable "
            "sampler interfaces, and efficiency claims are deferred to K03-K04."
        )
        self.assertTrue(any(
            "generic executable ownership must remain assigned only to F06A" in error
            for error in self.errors(nodes=false_deferral)
        ))

        false_f07a_ownership = copy.deepcopy(self.nodes)
        f06 = next(node for node in false_f07a_ownership["nodes"]
                   if node["id"] == "F06-CL")
        f06["boundary_hypotheses"] = f06["boundary_hypotheses"].replace(
            "F06A-EXECUTABLE-CL alone owns the binary-string representation, six-input "
            "dimension/marginal/linear/factor query machine with canonical blank normalization, "
            "associated sampler distribution and step count, valid-query finite maximum "
            "and global positive-index RuntimeBigO, executable downsizing transformation, "
            "dimension s(n) * log q(n), associated downsized maps, and O(TIME_S(n) "
            "log q(n)) runtime at conditionally-linear.tex:553-712.",
            "F07A-DETYPING and QPBT-043 own the generic executable layer instead.",
        )
        self.assertTrue(any(
            "generic executable ownership must remain assigned only to F06A" in error
            for error in self.errors(nodes=false_f07a_ownership)
        ))

        vague_detyping = copy.deepcopy(self.nodes)
        detyping = next(node for node in vague_detyping["nodes"]
                        if node["id"] == check.DETYPING_OWNER_ID)
        detyping["boundary_hypotheses"] = (
            "The machine layer is deferred to later complexity work in K03 and K04."
        )
        self.assertTrue(any(
            "executable representation and cost ownership must remain concrete" in error
            for error in self.errors(nodes=vague_detyping)
        ))

    def test_lean_api_compatibility_contract_is_explicit(self) -> None:
        by_id = {node["id"]: node for node in self.nodes["nodes"]}

        field = by_id["F01-FIELD"]
        self.assertIn("GaloisField 2 k", field["statement"])
        for instance in ("Field", "Fintype", "DecidableEq", "CharP"):
            self.assertIn(instance, field["encoding"])
        self.assertNotIn("FieldModel", json.dumps(field, sort_keys=True))

        measurement = by_id["F03-MEASUREMENT"]
        self.assertIn("MIPStarRE.Quantum.Measurement", measurement["encoding"])
        self.assertIn("do not open", measurement["encoding"])
        self.assertIn("universe uOutcome uCoord", measurement["boundary_hypotheses"])
        self.assertIn("[Fintype Outcome]", measurement["boundary_hypotheses"])

        strategy = by_id["F04-DISTANCE"]
        self.assertIn("EuclideanSpace", strategy["encoding"])
        self.assertIn("Matrix.toEuclideanLin.symm", strategy["encoding"])
        self.assertIn("norm-one", strategy["encoding"])
        self.assertIn("MIPStarRE.QPBT.BipartiteIsometry", strategy["lean"]["names"])
        self.assertIn("MIPStarRE.QPBT.BipartiteIsometry.conjugateAlice",
                      strategy["lean"]["names"])
        self.assertIn("MIPStarRE.QPBT.BipartiteIsometry.conjugateBob",
                      strategy["lean"]["names"])
        self.assertIn("all question, outcome, local, auxiliary, junk, and ideal universes",
                      strategy["boundary_hypotheses"])

        parameters = by_id["G01-PARAMETERS"]
        self.assertIn("q=2^k", parameters["statement"])
        self.assertIn("Odd k", parameters["encoding"])
        self.assertIn("Dvd.dvd params.m params.q", parameters["encoding"])
        self.assertIn("not an alias of LDT.Parameters", parameters["encoding"])
        self.assertNotIn("LDT", parameters["lean"]["module"])

        game = by_id["G02-GAME"]
        for phrase in ("sigma types", "uniform finite POVM alphabet", "PMF"):
            self.assertIn(phrase, game["encoding"])
        self.assertIn("universe uType uQuestion uAnswer", game["boundary_hypotheses"])

        extraction = by_id["A15-UNITARY"]
        self.assertIn("MIPStarRE.QPBT.Realizes", extraction["lean"]["names"])
        self.assertIn("MIPStarRE.QPBT.SquaredRealizes", extraction["lean"]["names"])
        for family in ("Alice-X", "Alice-Z", "Bob-X", "Bob-Z"):
            self.assertIn(family, extraction["encoding"])
        self.assertIn("one squared mapped-state norm bound <= delta",
                      extraction["encoding"])
        self.assertIn("unsquared mapped-state norm bound", extraction["encoding"])
        self.assertIn("each <= delta", extraction["encoding"])

        robustness = by_id["R05-ROBUSTNESS"]
        soundness = by_id["S01-SOUNDNESS"]
        self.assertIn("SquaredRealizes", robustness["statement"])
        self.assertIn("normExtraction_ofSquared", robustness["statement"])
        self.assertIn("unsquared Realizes", robustness["statement"])
        self.assertIn("Real.rpow", robustness["encoding"])
        self.assertIn("Real.rpow", soundness["encoding"])
        self.assertEqual(["MIPStarRE.QPBT.pauliSoundness"], soundness["lean"]["names"])
        self.assertEqual(["N01-NAIMARK", "R05-ROBUSTNESS"], soundness["prerequisites"])
        self.assertIn("No bridge, extraction, witness, or projectivity assumption",
                      soundness["boundary_hypotheses"])

    def test_lean_plan_uses_breakable_identifier_macro(self) -> None:
        node = next(node for node in self.nodes["nodes"] if node["id"] == "F08-MAGIC-GAME")
        rendered = check.render_entry(node, [])
        self.assertIn(
            r"\BlueprintIdentifier{MIPStarRE.QPBT.magicSquareStrategyOfAnticommuting}",
            rendered,
        )
        self.assertIn(r"\linebreak", rendered)

    def test_additional_source_schema_and_rendering_are_checked(self) -> None:
        anchor = {
            "path": "references/2001.04383v3/sections/dependencies/measurements.tex",
            "label": "def:bracket",
            "generated_lines": [34, 47],
            "original_lines": [1887, 1900],
        }
        good = copy.deepcopy(self.nodes)
        good["nodes"][0]["additional_sources"] = [anchor]
        self.assertEqual([], self.errors(nodes=good))
        rendered = check.render_entry(good["nodes"][0], [])
        self.assertIn(r"\BlueprintField{Additional sources}", rendered)
        self.assertIn("measurements.tex:34-47", rendered)

        empty = copy.deepcopy(self.nodes)
        empty["nodes"][0]["additional_sources"] = []
        self.assertTrue(any("additional_sources must be a nonempty list" in error
                            for error in self.errors(nodes=empty)))

        malformed = copy.deepcopy(self.nodes)
        malformed["nodes"][0]["additional_sources"] = [{"path": "missing-fields.tex"}]
        self.assertTrue(any("additional_sources[0] must use the exact four-field schema" in error
                            for error in self.errors(nodes=malformed)))

        duplicate = copy.deepcopy(self.nodes)
        duplicate["nodes"][0]["additional_sources"] = [
            copy.deepcopy(duplicate["nodes"][0]["source"])
        ]
        self.assertTrue(any("duplicate source anchor" in error
                            for error in self.errors(nodes=duplicate)))

    def test_machine_visible_implementation_contract_is_checked(self) -> None:
        good = copy.deepcopy(self.nodes)
        node = next(item for item in good["nodes"] if item["id"] == "F01-FIELD")
        self.assertEqual([], self.errors(nodes=good))
        rendered = check.render_entry(node, [])
        self.assertIn(r"\BlueprintField{Writer lane}{field}", rendered)
        self.assertIn(r"\BlueprintField{Owned Lean file}", rendered)
        self.assertIn(r"\BlueprintField{Signature manifest}", rendered)

        self.assertEqual(
            {"field", "approximation", "polynomial", "pauli", "types", "parameters"},
            check.IMPLEMENTATION_WRITER_LANES,
        )
        for writer_lane in sorted(check.IMPLEMENTATION_WRITER_LANES):
            with self.subTest(writer_lane=writer_lane):
                admitted = copy.deepcopy(good)
                admitted["nodes"][0]["implementation_contract"]["writer_lane"] = writer_lane
                self.assertEqual([], self.errors(nodes=admitted))

        for field, value, phrase in (
            ("writer_lane", "unknown", "invalid implementation writer lane"),
            ("owned_file", "../Field.lean", "invalid implementation owned file"),
            ("signature_manifest", {
                **node["implementation_contract"]["signature_manifest"],
                "sha256": "0" * 64,
            }, "signature manifest hash mismatch"),
            ("validation_commands", ["lake build"], "omits scoped Lean command"),
            ("allowed_minimal_sorries", ["MIPStarRE.QPBT.pauliSoundness"],
             "permits foreign sorries"),
            ("proof_complete_sorry_count", 1, "must permit zero sorries"),
        ):
            with self.subTest(field=field):
                bad = copy.deepcopy(good)
                bad["nodes"][0]["implementation_contract"][field] = value
                self.assertTrue(any(phrase in error for error in self.errors(nodes=bad)))

        bad_marker = copy.deepcopy(good)
        bad_marker["nodes"][0]["implementation_contract"]["signature_manifest"][
            "begin_marker"
        ] = "<!-- BEGIN MISSING -->"
        self.assertTrue(any("markers must be unique and ordered" in error
                            for error in self.errors(nodes=bad_marker)))

        bad_path = copy.deepcopy(good)
        bad_path["nodes"][0]["implementation_contract"]["signature_manifest"][
            "path"
        ] = "../outside.md"
        self.assertTrue(any("invalid signature manifest path" in error
                            for error in self.errors(nodes=bad_path)))

        missing_name = copy.deepcopy(good)
        missing_name["nodes"][0]["lean"]["names"].append(
            "MIPStarRE.QPBT.declarationAbsentFromManifest"
        )
        self.assertTrue(any("signature manifest omits planned declaration" in error
                            for error in self.errors(nodes=missing_name)))

    def test_rendering_is_deterministic(self) -> None:
        first = check.outputs(self.nodes, self.gaps, self.externals)
        second = check.outputs(copy.deepcopy(self.nodes), copy.deepcopy(self.gaps),
                               copy.deepcopy(self.externals))
        self.assertEqual(first, second)

    def test_source_anchor_checks_label_and_original_line_mapping(self) -> None:
        node = copy.deepcopy(self.nodes["nodes"][0])
        node["source"] = {
            "path": "references/2001.04383v3/sections/dependencies/sample.tex",
            "label": "def:sample",
            "generated_lines": [2, 2],
            "original_lines": [101, 101],
        }
        node["additional_sources"] = [{
            "path": "references/2001.04383v3/sections/dependencies/sample.tex",
            "label": "",
            "generated_lines": [1, 1],
            "original_lines": [100, 100],
        }]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "sections/dependencies").mkdir(parents=True)
            (root / "sections/dependencies/sample.tex").write_bytes(
                b"header\r\n\\label{def:sample}\r\n"
            )
            manifest = {
                "collections": [{
                    "output_directory": "dependencies",
                    "slices": [["sample", 100, 101]],
                }]
            }
            (root / "split-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            doc = {"nodes": [node]}
            self.assertEqual([], check.validate_sources(doc, root))
            node["additional_sources"][0]["original_lines"] = [101, 101]
            self.assertTrue(any("additional_sources[0]" in error and
                                "mapping mismatch" in error
                                for error in check.validate_sources(doc, root)))
            node["additional_sources"][0]["original_lines"] = [100, 100]
            node["source"]["original_lines"] = [100, 100]
            self.assertTrue(any("mapping mismatch" in error
                                for error in check.validate_sources(doc, root)))
            node["source"]["original_lines"] = [101, 101]
            node["source"]["label"] = "def:absent"
            self.assertTrue(any("label" in error for error in check.validate_sources(doc, root)))
            self.assertTrue(any(
                "source root lacks split manifest" in error
                for error in check.validate_sources(doc, root / "standalone-stage-3")
            ))


class BlueprintPdfCheckTests(unittest.TestCase):
    def test_bbox_rejects_zero_pages(self) -> None:
        pages, errors = check_pdf.validate_bbox("<html><body><doc/></body></html>")
        self.assertEqual(0, pages)
        self.assertEqual(["document contains no pages"], errors)

    def test_bbox_rejects_zero_area_word_boxes(self) -> None:
        xml = """<html><body><doc><page width="100" height="200">
          <word xMin="10" yMin="20" xMax="10" yMax="30">zero-width</word>
          <word xMin="20" yMin="40" xMax="30" yMax="40">zero-height</word>
        </page></doc></body></html>"""
        pages, errors = check_pdf.validate_bbox(xml)
        self.assertEqual(1, pages)
        self.assertEqual(2, len(errors))
        self.assertTrue(all("zero-area word box" in error for error in errors))

    def test_bbox_rejects_text_past_every_physical_page_edge(self) -> None:
        xml = """<?xml version="1.0"?>
        <html xmlns="http://www.w3.org/1999/xhtml"><body><doc>
          <page width="100" height="200">
            <flow><block><line>
              <word xMin="-1" yMin="20" xMax="10" yMax="21">left</word>
              <word xMin="90" yMin="40" xMax="101" yMax="41">right</word>
              <word xMin="20" yMin="-1" xMax="30" yMax="2">bottom</word>
              <word xMin="40" yMin="199" xMax="50" yMax="201">top</word>
            </line></block></flow>
          </page>
        </doc></body></html>"""
        pages, errors = check_pdf.validate_bbox(xml)
        self.assertEqual(1, pages)
        self.assertEqual(4, len(errors))
        for edge in ("left", "right", "bottom", "top"):
            self.assertTrue(any(f"crosses {edge} page boundary" in error
                                for error in errors))

    def test_bbox_rejects_malformed_or_nonfinite_geometry(self) -> None:
        xml = """<html><body><doc><page width="100" height="200">
          <word xMin="10" yMin="1" xMax="1" yMax="2">inverted</word>
          <word xMin="nan" yMin="1" xMax="10" yMax="2">nonfinite</word>
          <word xMin="1" yMin="1" xMax="10">missing</word>
        </page><page width="-1" height="200"/></doc></body></html>"""
        pages, errors = check_pdf.validate_bbox(xml)
        self.assertEqual(2, pages)
        self.assertEqual(4, len(errors))
        self.assertTrue(any("inverted word box" in error for error in errors))
        self.assertTrue(any("non-finite word box" in error for error in errors))
        self.assertTrue(any("malformed word box" in error for error in errors))
        self.assertTrue(any("invalid page dimensions" in error for error in errors))

    def test_bbox_rejects_overlap_and_accepts_adjacent_text(self) -> None:
        collision_xml = """<html><body><doc><page width="100" height="200">
          <word xMin="10" yMin="20" xMax="30" yMax="30">source-anchor</word>
          <word xMin="25" yMin="20" xMax="40" yMax="30">disposition</word>
        </page></doc></body></html>"""
        pages, errors = check_pdf.validate_bbox(collision_xml)
        self.assertEqual(1, pages)
        self.assertEqual(1, len(errors))
        self.assertIn("text boxes overlap (5.000 x 10.000 points)", errors[0])
        self.assertIn("'source-anchor' and 'disposition'", errors[0])

        xml = """<html xmlns="http://www.w3.org/1999/xhtml"><body><doc>
          <page width="100" height="200">
            <word xMin="1" yMin="1" xMax="50" yMax="2">first</word>
            <word xMin="50" yMin="1" xMax="100" yMax="2">second</word>
          </page>
        </doc></body></html>"""
        pages, errors = check_pdf.validate_bbox(xml)
        self.assertEqual(1, pages)
        self.assertEqual([], errors)
        self.assertEqual([], check_pdf.extracted_identifier_errors(
            "magicSquareStrategyOf\nAnticommuting",
            ["magicSquareStrategyOfAnticommuting"],
        ))

    def test_bbox_overlap_threshold_is_strict_and_decimal_exact(self) -> None:
        cases = (
            ("x", "9.9001", "0", "accepts just below", 0),
            ("x", "9.9", "0", "accepts exact threshold", 0),
            ("x", "9.8999", "0", "rejects just above", 1),
            ("y", "9", "9.9001", "accepts just below", 0),
            ("y", "9", "9.9", "accepts exact threshold", 0),
            ("y", "9", "9.8999", "rejects just above", 1),
        )
        for axis, x_min, y_min, description, expected_errors in cases:
            with self.subTest(axis=axis, position=description):
                xml = f"""<html><body><doc><page width="100" height="200">
                  <word xMin="0" yMin="0" xMax="10" yMax="10">first</word>
                  <word xMin="{x_min}" yMin="{y_min}" xMax="20" yMax="20">second</word>
                </page></doc></body></html>"""
                pages, errors = check_pdf.validate_bbox(xml)
                self.assertEqual(1, pages)
                self.assertEqual(expected_errors, len(errors))


if __name__ == "__main__":
    unittest.main()
