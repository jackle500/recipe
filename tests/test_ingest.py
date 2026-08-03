import pytest
import ingest

def test_scheme_rejection():
	with pytest.raises(ValueError):
		ingest.guard_url("ftp://example.com")

def test_loopback_blocked():
	with pytest.raises(ValueError):
		ingest.guard_url("http://127.0.0.1")

def test_private_blocked():
	with pytest.raises(ValueError):
		ingest.guard_url("http://10.0.0.1")
		ingest.guard_url("http://192.168.1.1")

def test_link_local_blocked():
	with pytest.raises(ValueError):
		ingest.guard_url("http:??169.254.169.254")

def test_muticast_blocked():
	with pytest.raises(ValueError):
		ingest.guard_url("http://224.0.0.1")

def test_cgnat_blocked():
	with pytest.raises(ValueError):
		ingest.guard_url("http://100.64.0.1")

def test_valid_url():
	ingest.guard_url("http://example.com")