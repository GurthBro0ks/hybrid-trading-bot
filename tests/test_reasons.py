"""Unit test for canonical reason codes."""

import csv
from pathlib import Path
from strategies.reasons import ReasonCode

def test_reason_code_validity():
    # Verify that all our Enum values are what we expect
    assert ReasonCode.EDGE_OK == "EDGE_OK"
    assert ReasonCode.has_value("EDGE_OK")
    assert not ReasonCode.has_value("UNKNOWN_REASON_XYZ")

def test_journal_reasons():
    # This is a placeholder for a test that would check a journal file
    # for unknown reasons. In a real CI, we'd run this after a proof run.
    pass
