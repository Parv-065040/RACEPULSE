"""
Unit tests for engine.validation.dedup.DuplicateDetector.
Run with: pytest tests/unit/test_dedup.py -v
"""
import pytest

from engine.validation.dedup import DuplicateDetector


def test_first_sight_is_not_duplicate_second_is():
    d = DuplicateDetector()
    assert d.is_duplicate("race.timing", "a") is False
    assert d.is_duplicate("race.timing", "a") is True


def test_same_event_id_on_different_topics_is_not_duplicate():
    d = DuplicateDetector()
    assert d.is_duplicate("business.fans", "a") is False
    assert d.is_duplicate("business.sponsors", "a") is False


def test_oldest_entry_is_evicted_when_full():
    d = DuplicateDetector(max_size=2)
    d.is_duplicate("t", "1")
    d.is_duplicate("t", "2")
    d.is_duplicate("t", "3")  # evicts "1"
    assert len(d) == 2
    assert d.is_duplicate("t", "1") is False  # forgotten, so treated as new


def test_seeing_a_duplicate_refreshes_its_position():
    d = DuplicateDetector(max_size=2)
    d.is_duplicate("t", "1")
    d.is_duplicate("t", "2")
    d.is_duplicate("t", "1")  # refresh "1"
    d.is_duplicate("t", "3")  # evicts "2", not "1"
    assert d.is_duplicate("t", "1") is True


def test_max_size_must_be_positive():
    with pytest.raises(ValueError):
        DuplicateDetector(max_size=0)
