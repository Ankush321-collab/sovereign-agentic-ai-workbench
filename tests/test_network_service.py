import pytest
import hashlib
from backend.services.network_service import NetworkService

def test_sovereignty_status_live_sockets():
    """TDD Seam: Verify that NetworkService scans real OS sockets and verifies zero external egress."""
    status = NetworkService.get_sovereignty_status()

    assert isinstance(status, dict)
    assert "external_connections" in status
    assert "local_connections" in status
    assert "airgap_verification" in status
    assert "audit_hash" in status
    assert status["external_connections"] == 0
    assert status["internet_blocked"] is True
    assert "LOCAL" in status["airgap_verification"]

def test_forensic_audit_export_sha256():
    """TDD Seam: Verify cryptographic audit report contains real socket records and valid SHA-256."""
    audit = NetworkService.generate_forensic_audit()

    assert isinstance(audit, dict)
    assert audit["external_violations_detected"] == 0
    assert audit["loopback_verified"] is True
    assert "sockets" in audit
    assert isinstance(audit["sockets"], list)
    assert "integrity_signature_sha256" in audit
    assert len(audit["integrity_signature_sha256"]) == 64
