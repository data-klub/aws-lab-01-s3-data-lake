"""Checks that the package imports, the config matches docs/spec.md, and Lab 01 stays seeded."""

import importlib.util
import random
from pathlib import Path

import yaml

import house_prices_generator

ROOT = Path(__file__).resolve().parents[1]


def test_package_imports() -> None:
    assert house_prices_generator.__version__


def test_generator_config() -> None:
    config = yaml.safe_load((ROOT / "config" / "generator.yaml").read_text(encoding="utf-8"))
    assert config["seed"] == 42
    assert config["backfill_days"] == 30
    assert config["properties"] == 20000
    assert config["api"]["rate_limit_per_minute"] == 300


def test_lab01_generator_is_deterministic() -> None:
    path = ROOT / "labs" / "01-s3-data-lake" / "generate.py"
    spec = importlib.util.spec_from_file_location("lab01_generate", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    first = [module.make_listing(random.Random(42), i) for i in range(3)]
    second = [module.make_listing(random.Random(42), i) for i in range(3)]
    assert first == second
    assert {row["district"] for row in first} <= set(module.DISTRICTS)
