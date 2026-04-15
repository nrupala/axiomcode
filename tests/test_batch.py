"""Test suite for 100-program batch generation and validation.

Tests cover:
- Algorithm definition completeness
- Generated Lean file correctness
- Spec generation pipeline
- Certificate generation
- UTF-8 encoding enforcement
- End-to-end pipeline
- Category and difficulty coverage
- Report integrity
"""

import pytest
import sys
import os
import json
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


# ─── Algorithm Definitions Tests ────────────────────────────────────────────

class TestAlgorithmDefinitions:
    def test_100_algorithms_defined(self):
        from batch_generate import ALGORITHMS
        assert len(ALGORITHMS) == 100

    def test_all_ids_unique(self):
        from batch_generate import ALGORITHMS
        ids = [a["id"] for a in ALGORITHMS]
        assert len(ids) == len(set(ids))
        assert ids == list(range(1, 101))

    def test_all_names_unique(self):
        from batch_generate import ALGORITHMS
        names = [a["name"] for a in ALGORITHMS]
        assert len(names) == len(set(names))

    def test_all_names_lowercase_underscore(self):
        from batch_generate import ALGORITHMS
        for a in ALGORITHMS:
            assert a["name"] == a["name"].lower()
            assert " " not in a["name"]

    def test_all_have_required_fields(self):
        from batch_generate import ALGORITHMS
        required = ["id", "name", "category", "description", "difficulty", "proof_complexity"]
        for a in ALGORITHMS:
            for field in required:
                assert field in a, f"Algorithm {a['id']} missing field: {field}"

    def test_all_descriptions_non_empty(self):
        from batch_generate import ALGORITHMS
        for a in ALGORITHMS:
            assert len(a["description"]) > 20, f"Algorithm {a['id']} description too short"

    def test_valid_difficulty_levels(self):
        from batch_generate import ALGORITHMS
        valid = {"Easy", "Medium", "Hard"}
        for a in ALGORITHMS:
            assert a["difficulty"] in valid, f"Algorithm {a['id']} has invalid difficulty: {a['difficulty']}"

    def test_valid_proof_complexity(self):
        from batch_generate import ALGORITHMS
        valid = {"Low", "Medium", "High"}
        for a in ALGORITHMS:
            assert a["proof_complexity"] in valid, f"Algorithm {a['id']} has invalid proof_complexity: {a['proof_complexity']}"

    def test_valid_categories(self):
        from batch_generate import ALGORITHMS
        valid = {
            "Sorting", "Searching", "Number Theory", "Data Structures",
            "Graph", "Dynamic Programming", "String", "Mathematical",
            "Greedy", "Backtracking",
        }
        for a in ALGORITHMS:
            assert a["category"] in valid, f"Algorithm {a['id']} has invalid category: {a['category']}"

    def test_category_coverage_minimum(self):
        from batch_generate import ALGORITHMS
        categories = set(a["category"] for a in ALGORITHMS)
        assert len(categories) >= 10, f"Expected at least 10 categories, got {len(categories)}"

    def test_sorting_algorithms_count(self):
        from batch_generate import ALGORITHMS
        sorting = [a for a in ALGORITHMS if a["category"] == "Sorting"]
        assert len(sorting) >= 10, f"Expected 10+ sorting algorithms, got {len(sorting)}"

    def test_graph_algorithms_count(self):
        from batch_generate import ALGORITHMS
        graph = [a for a in ALGORITHMS if a["category"] == "Graph"]
        assert len(graph) >= 10, f"Expected 10+ graph algorithms, got {len(graph)}"

    def test_data_structures_count(self):
        from batch_generate import ALGORITHMS
        ds = [a for a in ALGORITHMS if a["category"] == "Data Structures"]
        assert len(ds) >= 10, f"Expected 10+ data structure algorithms, got {len(ds)}"

    def test_difficulty_distribution(self):
        from batch_generate import ALGORITHMS
        difficulties = {}
        for a in ALGORITHMS:
            difficulties[a["difficulty"]] = difficulties.get(a["difficulty"], 0) + 1
        assert difficulties.get("Easy", 0) >= 10
        assert difficulties.get("Medium", 0) >= 10
        assert difficulties.get("Hard", 0) >= 10


# ─── Spec Generation Tests ──────────────────────────────────────────────────

class TestSpecGeneration:
    def test_mock_spec_generates_for_all(self):
        from batch_generate import ALGORITHMS, generate_mock_spec
        for a in ALGORITHMS:
            spec = generate_mock_spec(a)
            assert spec is not None
            assert spec.theorem != ""
            assert len(spec.imports) >= 2

    def test_spec_has_correct_imports(self):
        from batch_generate import ALGORITHMS, generate_mock_spec
        for a in ALGORITHMS:
            spec = generate_mock_spec(a)
            assert "Mathlib" in spec.imports
            assert "Aesop" in spec.imports

    def test_spec_has_docstring(self):
        from batch_generate import ALGORITHMS, generate_mock_spec
        for a in ALGORITHMS:
            spec = generate_mock_spec(a)
            assert spec.docstring != ""

    def test_spec_has_theorem(self):
        from batch_generate import ALGORITHMS, generate_mock_spec
        for a in ALGORITHMS:
            spec = generate_mock_spec(a)
            assert "theorem" in spec.theorem.lower()
            assert "by sorry" in spec.theorem

    def test_spec_has_hash(self):
        from batch_generate import ALGORITHMS, generate_mock_spec
        for a in ALGORITHMS:
            spec = generate_mock_spec(a)
            assert spec.spec_hash != ""
            assert len(spec.spec_hash) >= 32

    def test_spec_hash_unique_per_algorithm(self):
        from batch_generate import ALGORITHMS, generate_mock_spec
        hashes = set()
        for a in ALGORITHMS:
            spec = generate_mock_spec(a)
            hashes.add(spec.spec_hash)
        assert len(hashes) == 100, "Each algorithm should produce a unique spec hash"

    def test_spec_to_lean_output(self):
        from batch_generate import ALGORITHMS, generate_mock_spec
        for a in ALGORITHMS:
            spec = generate_mock_spec(a)
            lean = spec.to_lean()
            assert "import" in lean
            assert "theorem" in lean

    def test_spec_generation_time_positive(self):
        from batch_generate import ALGORITHMS, generate_mock_spec
        for a in ALGORITHMS:
            spec = generate_mock_spec(a)
            assert spec.generation_time_ms >= 0

    def test_spec_model_used(self):
        from batch_generate import ALGORITHMS, generate_mock_spec
        for a in ALGORITHMS:
            spec = generate_mock_spec(a)
            assert spec.model_used == "mock"

    def test_spec_source_nl_preserved(self):
        from batch_generate import ALGORITHMS, generate_mock_spec
        for a in ALGORITHMS:
            spec = generate_mock_spec(a)
            assert spec.source_nl == a["description"]


# ─── Spec Validation Tests ──────────────────────────────────────────────────

class TestSpecValidation:
    def test_all_specs_validate(self):
        from batch_generate import ALGORITHMS, generate_mock_spec, validate_spec
        for a in ALGORITHMS:
            spec = generate_mock_spec(a)
            is_valid, error = validate_spec(spec)
            assert is_valid, f"Algorithm {a['id']} ({a['name']}) failed validation: {error}"

    def test_valid_spec_has_imports(self):
        from batch_generate import validate_spec
        from cli import LeanSpec
        spec = LeanSpec(theorem="theorem test : True := by sorry", imports=["Mathlib"], docstring="test", generation_time_ms=100.0)
        spec.compute_hash()
        is_valid, error = validate_spec(spec)
        assert is_valid

    def test_invalid_spec_no_imports(self):
        from batch_generate import validate_spec
        from cli import LeanSpec
        spec = LeanSpec(theorem="theorem test : True := by sorry", imports=[], docstring="test")
        spec.compute_hash()
        is_valid, error = validate_spec(spec)
        assert not is_valid
        assert "No imports" in error

    def test_invalid_spec_no_theorem(self):
        from batch_generate import validate_spec
        from cli import LeanSpec
        spec = LeanSpec(theorem="", imports=["Mathlib"], docstring="test")
        spec.compute_hash()
        is_valid, error = validate_spec(spec)
        assert not is_valid
        assert "No theorem" in error

    def test_invalid_spec_no_docstring(self):
        from batch_generate import validate_spec
        from cli import LeanSpec
        spec = LeanSpec(theorem="theorem test : True := by sorry", imports=["Mathlib"], docstring="")
        spec.compute_hash()
        is_valid, error = validate_spec(spec)
        assert not is_valid
        assert "No docstring" in error

    def test_invalid_spec_no_proof_mode(self):
        from batch_generate import validate_spec
        from cli import LeanSpec
        spec = LeanSpec(theorem="theorem test : True", imports=["Mathlib"], docstring="test")
        spec.compute_hash()
        is_valid, error = validate_spec(spec)
        assert not is_valid
        assert "proof mode" in error.lower()


# ─── Generated Lean File Tests ──────────────────────────────────────────────

class TestGeneratedLeanFiles:
    @pytest.fixture(scope="class")
    def lean_dir(self):
        return Path(__file__).parent.parent / "batch_generated" / "lean"

    def test_lean_directory_exists(self, lean_dir):
        assert lean_dir.exists()

    def test_100_lean_files_generated(self, lean_dir):
        files = list(lean_dir.glob("*.lean"))
        assert len(files) == 100, f"Expected 100 .lean files, got {len(files)}"

    def test_all_lean_files_have_correct_names(self, lean_dir):
        from batch_generate import ALGORITHMS
        files = {f.stem for f in lean_dir.glob("*.lean")}
        expected = {a["name"] for a in ALGORITHMS}
        assert files == expected, f"Missing: {expected - files}, Extra: {files - expected}"

    def test_lean_files_are_utf8(self, lean_dir):
        for f in lean_dir.glob("*.lean"):
            content = f.read_text(encoding="utf-8")
            assert len(content) > 0

    def test_lean_files_contain_imports(self, lean_dir):
        for f in lean_dir.glob("*.lean"):
            content = f.read_text(encoding="utf-8")
            assert "import" in content, f"{f.name} has no imports"

    def test_lean_files_contain_theorem(self, lean_dir):
        for f in lean_dir.glob("*.lean"):
            content = f.read_text(encoding="utf-8")
            assert "theorem" in content, f"{f.name} has no theorem"

    def test_lean_files_contain_by_sorry(self, lean_dir):
        for f in lean_dir.glob("*.lean"):
            content = f.read_text(encoding="utf-8")
            assert "by sorry" in content, f"{f.name} has no proof placeholder"

    def test_lean_files_contain_docstring(self, lean_dir):
        for f in lean_dir.glob("*.lean"):
            content = f.read_text(encoding="utf-8")
            assert "/--" in content, f"{f.name} has no docstring"

    def test_lean_file_size_reasonable(self, lean_dir):
        for f in lean_dir.glob("*.lean"):
            size = f.stat().st_size
            assert 50 < size < 5000, f"{f.name} has unusual size: {size}"

    def test_specific_lean_file_binary_search(self, lean_dir):
        f = lean_dir / "binary_search.lean"
        assert f.exists()
        content = f.read_text(encoding="utf-8")
        assert "import Mathlib" in content
        assert "theorem" in content
        assert "binary_search" in content

    def test_specific_lean_file_merge_sort(self, lean_dir):
        f = lean_dir / "merge_sort.lean"
        assert f.exists()
        content = f.read_text(encoding="utf-8")
        assert "import Mathlib" in content
        assert "theorem" in content

    def test_specific_lean_file_dijkstra(self, lean_dir):
        f = lean_dir / "dijkstra_shortest_path.lean"
        assert f.exists()
        content = f.read_text(encoding="utf-8")
        assert "import" in content
        assert "theorem" in content


# ─── Batch Report Tests ─────────────────────────────────────────────────────

class TestBatchReport:
    @pytest.fixture(scope="class")
    def report_path(self):
        return Path(__file__).parent.parent / "batch_test_report.json"

    def test_report_file_exists(self, report_path):
        assert report_path.exists()

    def test_report_is_valid_json(self, report_path):
        data = json.loads(report_path.read_text(encoding="utf-8"))
        assert isinstance(data, dict)

    def test_report_has_all_fields(self, report_path):
        data = json.loads(report_path.read_text(encoding="utf-8"))
        required = ["timestamp", "total", "passed", "failed", "skipped", "total_time_ms", "pass_rate", "category_stats", "difficulty_stats", "results"]
        for field in required:
            assert field in data, f"Report missing field: {field}"

    def test_report_total_is_100(self, report_path):
        data = json.loads(report_path.read_text(encoding="utf-8"))
        assert data["total"] == 100

    def test_report_all_passed(self, report_path):
        data = json.loads(report_path.read_text(encoding="utf-8"))
        assert data["passed"] == 100
        assert data["failed"] == 0
        assert data["skipped"] == 0

    def test_report_pass_rate_100(self, report_path):
        data = json.loads(report_path.read_text(encoding="utf-8"))
        assert data["pass_rate"] == 100.0

    def test_report_results_count(self, report_path):
        data = json.loads(report_path.read_text(encoding="utf-8"))
        assert len(data["results"]) == 100

    def test_report_all_results_pass(self, report_path):
        data = json.loads(report_path.read_text(encoding="utf-8"))
        for r in data["results"]:
            assert r["status"] == "pass", f"Result {r['id']} ({r['name']}) is {r['status']}"

    def test_report_category_stats_complete(self, report_path):
        data = json.loads(report_path.read_text(encoding="utf-8"))
        total_in_categories = sum(s["total"] for s in data["category_stats"].values())
        assert total_in_categories == 100

    def test_report_difficulty_stats_complete(self, report_path):
        data = json.loads(report_path.read_text(encoding="utf-8"))
        total_in_difficulties = sum(s["total"] for s in data["difficulty_stats"].values())
        assert total_in_difficulties == 100

    def test_report_timestamp_present(self, report_path):
        data = json.loads(report_path.read_text(encoding="utf-8"))
        assert len(data["timestamp"]) > 0

    def test_report_total_time_positive(self, report_path):
        data = json.loads(report_path.read_text(encoding="utf-8"))
        assert data["total_time_ms"] > 0


# ─── Generated Specs JSON Tests ─────────────────────────────────────────────

class TestGeneratedSpecs:
    @pytest.fixture(scope="class")
    def specs_path(self):
        return Path(__file__).parent.parent / "batch_generated" / "specs.json"

    def test_specs_file_exists(self, specs_path):
        assert specs_path.exists()

    def test_specs_is_valid_json(self, specs_path):
        data = json.loads(specs_path.read_text(encoding="utf-8"))
        assert isinstance(data, list)

    def test_specs_count(self, specs_path):
        data = json.loads(specs_path.read_text(encoding="utf-8"))
        assert len(data) == 100

    def test_specs_have_required_fields(self, specs_path):
        data = json.loads(specs_path.read_text(encoding="utf-8"))
        required = ["id", "name", "category", "difficulty", "theorem", "imports", "definitions", "docstring", "spec_hash"]
        for spec in data:
            for field in required:
                assert field in spec, f"Spec {spec.get('id', '?')} missing field: {field}"

    def test_specs_theorems_contain_by_sorry(self, specs_path):
        data = json.loads(specs_path.read_text(encoding="utf-8"))
        for spec in data:
            assert "by sorry" in spec["theorem"], f"Spec {spec['id']} ({spec['name']}) missing proof placeholder"

    def test_specs_imports_include_mathlib(self, specs_path):
        data = json.loads(specs_path.read_text(encoding="utf-8"))
        for spec in data:
            assert "Mathlib" in spec["imports"], f"Spec {spec['id']} ({spec['name']}) missing Mathlib import"

    def test_specs_docstrings_present(self, specs_path):
        data = json.loads(specs_path.read_text(encoding="utf-8"))
        for spec in data:
            assert spec["docstring"] != "", f"Spec {spec['id']} ({spec['name']}) has empty docstring"

    def test_specs_hashes_unique(self, specs_path):
        data = json.loads(specs_path.read_text(encoding="utf-8"))
        hashes = [s["spec_hash"] for s in data]
        assert len(hashes) == len(set(hashes)), "Duplicate spec hashes found"

    def test_specs_are_utf8(self, specs_path):
        content = specs_path.read_text(encoding="utf-8")
        assert len(content) > 0


# ─── Certificate Generation Tests ───────────────────────────────────────────

class TestCertificateGeneration:
    def test_certificate_for_each_algorithm(self):
        from batch_generate import ALGORITHMS, generate_mock_spec
        from core.security import KeyStore, ProofCertificate
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            ks = KeyStore(tmpdir)
            kp = ks.create_key("batch_test", "test_pass")

            for a in ALGORITHMS:
                spec = generate_mock_spec(a)
                cert = ProofCertificate(
                    algorithm_name=a["name"],
                    spec_hash=spec.spec_hash,
                    proof_hash="mock_proof_hash",
                    theorem=spec.theorem,
                    steps=5,
                    lemmas=2,
                    model_used="mock",
                )
                cert.sign(kp.signing_key)
                assert cert.verify(kp.signing_key) is True
                assert cert.algorithm_name == a["name"]

    def test_certificate_tamper_detection(self):
        from batch_generate import ALGORITHMS, generate_mock_spec
        from core.security import KeyStore, ProofCertificate
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            ks = KeyStore(tmpdir)
            kp = ks.create_key("test", "pass")
            spec = generate_mock_spec(ALGORITHMS[0])

            cert = ProofCertificate(
                algorithm_name=spec.source_nl[:20],
                spec_hash=spec.spec_hash,
                proof_hash="mock",
                steps=5,
            )
            cert.sign(kp.signing_key)
            cert.steps = 999
            assert cert.verify(kp.signing_key) is False

    def test_certificate_save_load_roundtrip(self):
        from batch_generate import ALGORITHMS, generate_mock_spec
        from core.security import KeyStore, ProofCertificate
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            ks = KeyStore(tmpdir)
            kp = ks.create_key("test", "pass")
            spec = generate_mock_spec(ALGORITHMS[0])

            cert = ProofCertificate(
                algorithm_name="test_algo",
                spec_hash=spec.spec_hash,
                proof_hash="mock",
                steps=5,
                lemmas=2,
            )
            cert.sign(kp.signing_key)

            cert_path = Path(tmpdir) / "test.cert.json"
            cert.save(cert_path)
            loaded = ProofCertificate.load(cert_path)
            assert loaded.algorithm_name == cert.algorithm_name
            assert loaded.spec_hash == cert.spec_hash
            assert loaded.verify(kp.signing_key) is True


# ─── UTF-8 Encoding Tests ───────────────────────────────────────────────────

class TestUTF8Encoding:
    def test_pythonutf8_env_var(self):
        import batch_generate
        assert os.environ.get("PYTHONUTF8") == "1"

    def test_stdout_encoding(self):
        import sys
        assert sys.stdout.encoding == "utf-8"

    def test_stderr_encoding(self):
        import sys
        assert sys.stderr.encoding == "utf-8"

    def test_lean_files_written_utf8(self):
        lean_dir = Path(__file__).parent.parent / "batch_generated" / "lean"
        for f in lean_dir.glob("*.lean"):
            raw = f.read_bytes()
            try:
                raw.decode("utf-8")
            except UnicodeDecodeError:
                pytest.fail(f"{f.name} is not valid UTF-8")

    def test_report_written_utf8(self):
        report_path = Path(__file__).parent.parent / "batch_test_report.json"
        raw = report_path.read_bytes()
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError:
            pytest.fail("batch_test_report.json is not valid UTF-8")

    def test_specs_written_utf8(self):
        specs_path = Path(__file__).parent.parent / "batch_generated" / "specs.json"
        raw = specs_path.read_bytes()
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError:
            pytest.fail("specs.json is not valid UTF-8")


# ─── End-to-End Pipeline Tests ──────────────────────────────────────────────

class TestEndToEndPipeline:
    def test_full_pipeline_single_algorithm(self):
        from batch_generate import ALGORITHMS, generate_mock_spec, validate_spec
        from cli import LeanSpec
        from core.security import KeyStore, ProofCertificate
        import tempfile

        algo = ALGORITHMS[0]

        # Step 1: Generate spec
        spec = generate_mock_spec(algo)
        assert spec is not None

        # Step 2: Validate spec
        is_valid, error = validate_spec(spec)
        assert is_valid, f"Spec validation failed: {error}"

        # Step 3: Generate certificate
        with tempfile.TemporaryDirectory() as tmpdir:
            ks = KeyStore(tmpdir)
            kp = ks.create_key("e2e_test", "pass")

            cert = ProofCertificate(
                algorithm_name=algo["name"],
                spec_hash=spec.spec_hash,
                proof_hash="e2e_proof_hash",
                theorem=spec.theorem,
                steps=5,
                lemmas=2,
                model_used="mock",
            )
            cert.sign(kp.signing_key)
            assert cert.verify(kp.signing_key) is True

    def test_full_pipeline_random_algorithms(self):
        from batch_generate import ALGORITHMS, generate_mock_spec, validate_spec
        from core.security import KeyStore, ProofCertificate
        import tempfile
        import random

        random.seed(42)
        sample = random.sample(ALGORITHMS, 10)

        with tempfile.TemporaryDirectory() as tmpdir:
            ks = KeyStore(tmpdir)
            kp = ks.create_key("random_test", "pass")

            for algo in sample:
                spec = generate_mock_spec(algo)
                is_valid, error = validate_spec(spec)
                assert is_valid, f"{algo['name']}: {error}"

                cert = ProofCertificate(
                    algorithm_name=algo["name"],
                    spec_hash=spec.spec_hash,
                    proof_hash=f"proof_{algo['name']}",
                    theorem=spec.theorem,
                    steps=3,
                    lemmas=1,
                )
                cert.sign(kp.signing_key)
                assert cert.verify(kp.signing_key)

    def test_full_pipeline_hard_algorithms(self):
        from batch_generate import ALGORITHMS, generate_mock_spec, validate_spec
        from core.security import KeyStore, ProofCertificate
        import tempfile

        hard_algos = [a for a in ALGORITHMS if a["difficulty"] == "Hard"]
        assert len(hard_algos) > 0

        with tempfile.TemporaryDirectory() as tmpdir:
            ks = KeyStore(tmpdir)
            kp = ks.create_key("hard_test", "pass")

            for algo in hard_algos:
                spec = generate_mock_spec(algo)
                is_valid, error = validate_spec(spec)
                assert is_valid, f"Hard algorithm {algo['name']} failed: {error}"

                cert = ProofCertificate(
                    algorithm_name=algo["name"],
                    spec_hash=spec.spec_hash,
                    proof_hash=f"proof_{algo['name']}",
                    theorem=spec.theorem,
                    steps=10,
                    lemmas=5,
                )
                cert.sign(kp.signing_key)
                assert cert.verify(kp.signing_key)

    def test_full_pipeline_all_categories(self):
        from batch_generate import ALGORITHMS, generate_mock_spec, validate_spec
        from core.security import KeyStore, ProofCertificate
        import tempfile

        categories = set(a["category"] for a in ALGORITHMS)

        with tempfile.TemporaryDirectory() as tmpdir:
            ks = KeyStore(tmpdir)
            kp = ks.create_key("category_test", "pass")

            for cat in categories:
                algo = next(a for a in ALGORITHMS if a["category"] == cat)
                spec = generate_mock_spec(algo)
                is_valid, error = validate_spec(spec)
                assert is_valid, f"Category {cat} algorithm {algo['name']} failed: {error}"

                cert = ProofCertificate(
                    algorithm_name=algo["name"],
                    spec_hash=spec.spec_hash,
                    proof_hash=f"proof_{algo['name']}",
                    theorem=spec.theorem,
                    steps=5,
                    lemmas=2,
                )
                cert.sign(kp.signing_key)
                assert cert.verify(kp.signing_key)


# ─── Batch Generate Function Tests ──────────────────────────────────────────

class TestBatchGenerateFunction:
    def test_run_single_test_pass(self):
        from batch_generate import ALGORITHMS, run_single_test
        algo = ALGORITHMS[0]
        result = run_single_test(algo)
        assert result.status == "pass"
        assert result.spec_generated is True
        assert result.spec_valid is True

    def test_run_single_test_has_timing(self):
        from batch_generate import ALGORITHMS, run_single_test
        algo = ALGORITHMS[0]
        result = run_single_test(algo)
        assert result.generation_time_ms >= 0

    def test_run_single_test_has_hash(self):
        from batch_generate import ALGORITHMS, run_single_test
        algo = ALGORITHMS[0]
        result = run_single_test(algo)
        assert len(result.spec_hash) > 0

    def test_run_batch_test(self):
        from batch_generate import ALGORITHMS, run_batch_test
        report = run_batch_test(ALGORITHMS[:5])
        assert report.total == 5
        assert report.passed == 5
        assert report.failed == 0

    def test_run_batch_test_report_structure(self):
        from batch_generate import ALGORITHMS, run_batch_test
        report = run_batch_test(ALGORITHMS[:3])
        assert len(report.results) == 3
        assert len(report.category_stats) > 0
        assert len(report.difficulty_stats) > 0
        assert report.total_time_ms > 0


# ─── Import and Module Tests ────────────────────────────────────────────────

class TestModuleImports:
    def test_batch_generate_imports(self):
        import batch_generate
        assert hasattr(batch_generate, "ALGORITHMS")
        assert hasattr(batch_generate, "TestResult")
        assert hasattr(batch_generate, "BatchReport")
        assert hasattr(batch_generate, "generate_mock_spec")
        assert hasattr(batch_generate, "validate_spec")
        assert hasattr(batch_generate, "run_single_test")
        assert hasattr(batch_generate, "run_batch_test")

    def test_cli_integration(self):
        from batch_generate import generate_mock_spec
        from cli import _parse_spec, LeanSpec
        algo = {"id": 1, "name": "test", "category": "Sorting", "description": "test sort", "difficulty": "Easy", "proof_complexity": "Medium"}
        spec = generate_mock_spec(algo)
        assert isinstance(spec, LeanSpec)

    def test_security_integration(self):
        from batch_generate import ALGORITHMS, generate_mock_spec
        from core.security import ProofCertificate
        spec = generate_mock_spec(ALGORITHMS[0])
        cert = ProofCertificate(
            algorithm_name="test",
            spec_hash=spec.spec_hash,
            proof_hash="test",
        )
        assert cert.spec_hash == spec.spec_hash


# ─── Performance Tests ──────────────────────────────────────────────────────

class TestPerformance:
    def test_generate_100_specs_under_1s(self):
        from batch_generate import ALGORITHMS, generate_mock_spec
        start = time.monotonic()
        for a in ALGORITHMS:
            generate_mock_spec(a)
        elapsed = time.monotonic() - start
        assert elapsed < 1.0, f"Generating 100 specs took {elapsed:.2f}s, expected < 1s"

    def test_validate_100_specs_under_1s(self):
        from batch_generate import ALGORITHMS, generate_mock_spec, validate_spec
        start = time.monotonic()
        for a in ALGORITHMS:
            spec = generate_mock_spec(a)
            validate_spec(spec)
        elapsed = time.monotonic() - start
        assert elapsed < 1.0, f"Validating 100 specs took {elapsed:.2f}s, expected < 1s"

    def test_full_batch_under_5s(self):
        from batch_generate import ALGORITHMS, run_batch_test
        start = time.monotonic()
        report = run_batch_test(ALGORITHMS)
        elapsed = time.monotonic() - start
        assert elapsed < 5.0, f"Full batch took {elapsed:.2f}s, expected < 5s"
        assert report.passed == 100
