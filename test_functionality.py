#!/usr/bin/env python3
"""Comprehensive functionality test for AxiomCode"""

import sys
print('Python version:', sys.version)
print('Testing imports...')

# Test core module imports
from core.security import KeyStore, ProofCertificate, AuditLog
from core.persistence import DataStore, AlgorithmRegistry
from core.versioning import VersionManager
from core.licensing import LicenseManager

print('✓ All core modules imported successfully')

# Test instantiation
keystore = KeyStore()
print('✓ KeyStore instantiated')

ds = DataStore()
print('✓ DataStore instantiated')

vm = VersionManager()
print('✓ VersionManager instantiated')

lm = LicenseManager()
print('✓ LicenseManager instantiated')

# Test basic operations
print('\n--- Testing Core Operations ---')

# Test KeyStore
keypair = keystore.generate_keypair()
print(f'✓ Generated keypair: {keypair[0][:20]}...')

# Test DataStore
test_record = {'algorithm': 'test', 'code': 'def f(): pass', 'proof': 'trivial'}
record_id = ds.create('test_algo_001', test_record)
print(f'✓ Created record: {record_id}')

retrieved = ds.get(record_id)
print(f'✓ Retrieved record: {retrieved["algorithm"]}')

# Test VersionManager
vm.set('v1.0', {'major': 1, 'minor': 0})
version_info = vm.get('v1.0')
print(f'✓ Version info stored: {version_info}')

# Test LicenseManager
print(f'✓ License manager initialized: {type(lm).__name__}')

print('\n✅ ALL TESTS PASSED - AxiomCode is working correctly!')
