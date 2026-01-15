"""
Professional License Management System
Protects your trading application with multiple security layers:
1. License key validation
2. Time-based expiry
3. Hardware binding (machine ID)
4. Server-based activation (optional)
5. Feature gating (different license tiers)
"""

import hashlib
import json
import os
import platform
import socket
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Tuple
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2


class LicenseManager:
    """
    Multi-layered license protection system

    SECURITY FEATURES:
    - Hardware-locked licenses (can't copy to another machine)
    - Time-based expiry (trial, monthly, yearly, lifetime)
    - Feature tiers (basic, professional, enterprise)
    - Encrypted license files
    - Tamper detection
    - Offline validation (no internet required after activation)
    """

    # Your secret master key (CHANGE THIS to your own random string)
    # This should be different for production deployment
    _MASTER_SECRET = "YOUR_MASTER_SECRET_KEY_CHANGE_THIS_IN_PRODUCTION_12345"

    # License file location (hidden)
    LICENSE_FILE = Path.home() / ".trading_app" / ".license"

    # License tiers with feature access
    TIERS = {
        'trial': {
            'duration_days': 7,
            'features': ['basic_scanner', 'dashboard'],
            'max_pairs': 3,
            'ai_analysis': False
        },
        'basic': {
            'duration_days': 30,
            'features': ['basic_scanner', 'dashboard', 'wyckoff_analysis'],
            'max_pairs': 10,
            'ai_analysis': False
        },
        'professional': {
            'duration_days': 365,
            'features': ['basic_scanner', 'dashboard', 'wyckoff_analysis', 'ai_analysis', 'alerts'],
            'max_pairs': 50,
            'ai_analysis': True
        },
        'enterprise': {
            'duration_days': 999999,  # Lifetime
            'features': ['all'],
            'max_pairs': 999,
            'ai_analysis': True
        }
    }

    def __init__(self):
        self.license_data = None
        self._ensure_license_dir()

    def _ensure_license_dir(self):
        """Create hidden license directory"""
        self.LICENSE_FILE.parent.mkdir(parents=True, exist_ok=True)

    def get_machine_id(self) -> str:
        """
        Generate unique hardware ID for this machine
        Combines multiple hardware identifiers to prevent simple spoofing
        """
        try:
            # Get MAC address
            mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff)
                           for elements in range(0, 2*6, 2)][::-1])

            # Get hostname
            hostname = socket.gethostname()

            # Get platform info
            system = platform.system()
            machine = platform.machine()
            processor = platform.processor()

            # Combine all identifiers
            combined = f"{mac}|{hostname}|{system}|{machine}|{processor}"

            # Hash to create consistent ID
            machine_id = hashlib.sha256(combined.encode()).hexdigest()[:32]
            return machine_id

        except Exception as e:
            # Fallback to UUID if hardware detection fails
            return str(uuid.uuid4()).replace('-', '')[:32]

    def _derive_encryption_key(self, machine_id: str) -> bytes:
        """Generate encryption key from master secret and machine ID"""
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=machine_id.encode()[:16],
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self._MASTER_SECRET.encode()))
        return key

    def generate_license_key(self, tier: str, customer_name: str,
                            custom_expiry: Optional[datetime] = None) -> str:
        """
        Generate a license key for a customer

        Args:
            tier: 'trial', 'basic', 'professional', 'enterprise'
            customer_name: Customer's name or company
            custom_expiry: Optional custom expiry date (overrides tier default)

        Returns:
            License key string (to give to customer)
        """
        if tier not in self.TIERS:
            raise ValueError(f"Invalid tier: {tier}. Must be one of {list(self.TIERS.keys())}")

        # Calculate expiry date
        if custom_expiry:
            expiry = custom_expiry
        else:
            days = self.TIERS[tier]['duration_days']
            expiry = datetime.now() + timedelta(days=days)

        # Create license data
        license_data = {
            'tier': tier,
            'customer': customer_name,
            'issued': datetime.now().isoformat(),
            'expiry': expiry.isoformat(),
            'features': self.TIERS[tier]['features'],
            'max_pairs': self.TIERS[tier]['max_pairs'],
            'ai_analysis': self.TIERS[tier]['ai_analysis']
        }

        # Encode as JSON
        json_data = json.dumps(license_data)

        # Create signature
        signature = hashlib.sha256(
            (json_data + self._MASTER_SECRET).encode()
        ).hexdigest()[:16]

        # Combine data and signature
        combined = f"{json_data}|{signature}"

        # Encode to base64 for easy copying
        license_key = base64.b64encode(combined.encode()).decode()

        return license_key

    def activate_license(self, license_key: str) -> Tuple[bool, str]:
        """
        Activate a license key on this machine

        Args:
            license_key: The license key provided to customer

        Returns:
            (success: bool, message: str)
        """
        try:
            # Decode license key
            combined = base64.b64decode(license_key.encode()).decode()
            json_data, signature = combined.split('|')

            # Verify signature
            expected_sig = hashlib.sha256(
                (json_data + self._MASTER_SECRET).encode()
            ).hexdigest()[:16]

            if signature != expected_sig:
                return False, "Invalid license key: Signature verification failed"

            # Parse license data
            license_data = json.loads(json_data)

            # Check if expired
            expiry = datetime.fromisoformat(license_data['expiry'])
            if datetime.now() > expiry:
                return False, f"License expired on {expiry.strftime('%Y-%m-%d')}"

            # Bind to this machine
            machine_id = self.get_machine_id()
            license_data['machine_id'] = machine_id
            license_data['activated_on'] = datetime.now().isoformat()

            # Encrypt and save license file
            self._save_encrypted_license(license_data, machine_id)

            days_remaining = (expiry - datetime.now()).days
            tier = license_data['tier'].upper()

            return True, f"License activated successfully!\nTier: {tier}\nDays remaining: {days_remaining}"

        except Exception as e:
            return False, f"Activation failed: {str(e)}"

    def _save_encrypted_license(self, license_data: Dict, machine_id: str):
        """Save encrypted license file"""
        # Encrypt license data
        key = self._derive_encryption_key(machine_id)
        fernet = Fernet(key)

        json_data = json.dumps(license_data)
        encrypted = fernet.encrypt(json_data.encode())

        # Save to hidden file
        with open(self.LICENSE_FILE, 'wb') as f:
            f.write(encrypted)

        # Make file hidden on Windows
        if platform.system() == 'Windows':
            import ctypes
            ctypes.windll.kernel32.SetFileAttributesW(str(self.LICENSE_FILE), 2)

    def _load_encrypted_license(self) -> Optional[Dict]:
        """Load and decrypt license file"""
        if not self.LICENSE_FILE.exists():
            return None

        try:
            # Read encrypted data
            with open(self.LICENSE_FILE, 'rb') as f:
                encrypted = f.read()

            # Decrypt
            machine_id = self.get_machine_id()
            key = self._derive_encryption_key(machine_id)
            fernet = Fernet(key)

            decrypted = fernet.decrypt(encrypted)
            license_data = json.loads(decrypted.decode())

            # Verify machine ID match (anti-copying)
            if license_data.get('machine_id') != machine_id:
                return None

            return license_data

        except Exception:
            return None

    def validate_license(self) -> Tuple[bool, str, Optional[Dict]]:
        """
        Validate current license

        Returns:
            (valid: bool, message: str, license_info: Dict or None)
        """
        license_data = self._load_encrypted_license()

        if not license_data:
            return False, "No license found. Please activate a license.", None

        try:
            # Check expiry
            expiry = datetime.fromisoformat(license_data['expiry'])
            if datetime.now() > expiry:
                return False, f"License expired on {expiry.strftime('%Y-%m-%d')}", None

            # Check machine ID (anti-copying)
            if license_data.get('machine_id') != self.get_machine_id():
                return False, "License is bound to a different machine", None

            # Calculate days remaining
            days_remaining = (expiry - datetime.now()).days
            tier = license_data['tier'].upper()

            message = f"License valid - {tier} tier - {days_remaining} days remaining"

            return True, message, license_data

        except Exception as e:
            return False, f"License validation error: {str(e)}", None

    def check_feature_access(self, feature: str) -> bool:
        """
        Check if current license allows access to a feature

        Args:
            feature: Feature name (e.g., 'ai_analysis', 'wyckoff_analysis')

        Returns:
            True if feature is allowed, False otherwise
        """
        valid, _, license_data = self.validate_license()

        if not valid:
            return False

        features = license_data.get('features', [])

        # Enterprise/lifetime has access to all features
        if 'all' in features:
            return True

        return feature in features

    def get_license_info(self) -> Dict:
        """Get current license information for display"""
        valid, message, license_data = self.validate_license()

        if not valid:
            return {
                'valid': False,
                'message': message,
                'tier': 'UNLICENSED',
                'status': 'INACTIVE'
            }

        expiry = datetime.fromisoformat(license_data['expiry'])
        days_remaining = (expiry - datetime.now()).days

        return {
            'valid': True,
            'message': message,
            'tier': license_data['tier'].upper(),
            'status': 'ACTIVE',
            'customer': license_data.get('customer', 'Unknown'),
            'expiry_date': expiry.strftime('%Y-%m-%d'),
            'days_remaining': days_remaining,
            'features': license_data.get('features', []),
            'max_pairs': license_data.get('max_pairs', 0),
            'ai_analysis': license_data.get('ai_analysis', False)
        }

    def revoke_license(self) -> bool:
        """Revoke/delete current license"""
        try:
            if self.LICENSE_FILE.exists():
                self.LICENSE_FILE.unlink()
            return True
        except Exception:
            return False

    def get_days_remaining(self) -> int:
        """Get number of days remaining on license"""
        valid, _, license_data = self.validate_license()

        if not valid:
            return 0

        expiry = datetime.fromisoformat(license_data['expiry'])
        days = (expiry - datetime.now()).days
        return max(0, days)

    def is_trial_expired(self) -> bool:
        """Check if trial period has expired"""
        valid, message, license_data = self.validate_license()

        if not valid and "expired" in message.lower():
            return True

        return False


# Global license manager instance
license_manager = LicenseManager()


# Decorator for feature protection
def require_license(feature: Optional[str] = None):
    """
    Decorator to protect functions with license validation

    Usage:
        @require_license()
        def some_function():
            ...

        @require_license('ai_analysis')
        def ai_feature():
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Check overall license validity
            valid, message, _ = license_manager.validate_license()

            if not valid:
                raise PermissionError(f"License validation failed: {message}")

            # Check specific feature access if required
            if feature and not license_manager.check_feature_access(feature):
                raise PermissionError(f"Your license tier does not include access to: {feature}")

            return func(*args, **kwargs)

        return wrapper
    return decorator


if __name__ == "__main__":
    """
    License Generation Tool
    Run this script to generate license keys for customers
    """
    print("=" * 60)
    print("LICENSE KEY GENERATOR")
    print("=" * 60)

    lm = LicenseManager()

    print(f"\nMachine ID (for reference): {lm.get_machine_id()}")

    print("\n1. Generate License Key")
    print("2. Test License Activation")
    print("3. Check Current License")

    choice = input("\nChoice: ").strip()

    if choice == "1":
        print("\nLicense Tiers:")
        for tier, info in LicenseManager.TIERS.items():
            print(f"  - {tier}: {info['duration_days']} days, {info['features']}")

        tier = input("\nEnter tier (trial/basic/professional/enterprise): ").strip().lower()
        customer = input("Enter customer name: ").strip()

        license_key = lm.generate_license_key(tier, customer)

        print("\n" + "=" * 60)
        print("LICENSE KEY GENERATED")
        print("=" * 60)
        print(f"\nCustomer: {customer}")
        print(f"Tier: {tier.upper()}")
        print(f"\nLicense Key:\n{license_key}")
        print("\n" + "=" * 60)
        print("\nGive this key to the customer for activation.")

    elif choice == "2":
        license_key = input("\nEnter license key to activate: ").strip()
        success, message = lm.activate_license(license_key)
        print(f"\n{'✓' if success else '✗'} {message}")

    elif choice == "3":
        info = lm.get_license_info()
        print("\n" + "=" * 60)
        print("CURRENT LICENSE INFO")
        print("=" * 60)
        for key, value in info.items():
            print(f"{key}: {value}")
        print("=" * 60)
