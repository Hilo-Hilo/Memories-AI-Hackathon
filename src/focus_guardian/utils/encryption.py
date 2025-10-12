"""
Encryption utilities for securing API keys and sensitive data.

Uses Fernet symmetric encryption (AES 128-bit) for encrypting API keys
stored in configuration files.
"""

from cryptography.fernet import Fernet
from pathlib import Path
from typing import Optional

from ..utils.logger import get_logger

logger = get_logger(__name__)


class EncryptionManager:
    """Manages encryption/decryption of sensitive data."""
    
    def __init__(self, key_file: Path):
        """
        Initialize encryption manager.
        
        Args:
            key_file: Path to store/load encryption key
        """
        self.key_file = key_file
        self._fernet = self._get_or_create_key()
    
    def _get_or_create_key(self) -> Fernet:
        """Get existing encryption key or create new one."""
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                key = f.read()
            logger.debug(f"Loaded encryption key from {self.key_file}")
        else:
            key = Fernet.generate_key()
            self.key_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.key_file, 'wb') as f:
                f.write(key)
            
            # Secure the key file (Unix-like systems)
            import os
            if os.name != 'nt':  # Not Windows
                os.chmod(self.key_file, 0o600)
            
            logger.info(f"Generated new encryption key at {self.key_file}")
        
        return Fernet(key)
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext string.
        
        Args:
            plaintext: String to encrypt
            
        Returns:
            Base64-encoded encrypted string
        """
        try:
            encrypted = self._fernet.encrypt(plaintext.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt(self, encrypted_text: str) -> Optional[str]:
        """
        Decrypt encrypted string.
        
        Args:
            encrypted_text: Base64-encoded encrypted string
            
        Returns:
            Decrypted plaintext or None if decryption fails
        """
        try:
            decrypted = self._fernet.decrypt(encrypted_text.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return None
    
    def encrypt_dict(self, data: dict) -> dict:
        """
        Encrypt all string values in a dictionary.
        
        Args:
            data: Dictionary with string values
            
        Returns:
            Dictionary with encrypted values
        """
        encrypted_data = {}
        for key, value in data.items():
            if isinstance(value, str):
                encrypted_data[f"{key}_encrypted"] = self.encrypt(value)
            else:
                encrypted_data[key] = value
        return encrypted_data
    
    def decrypt_dict(self, data: dict) -> dict:
        """
        Decrypt all encrypted values in a dictionary.
        
        Args:
            data: Dictionary with encrypted values (keys ending in _encrypted)
            
        Returns:
            Dictionary with decrypted values
        """
        decrypted_data = {}
        for key, value in data.items():
            if key.endswith("_encrypted") and isinstance(value, str):
                original_key = key[:-10]  # Remove "_encrypted" suffix
                decrypted = self.decrypt(value)
                if decrypted:
                    decrypted_data[original_key] = decrypted
            else:
                decrypted_data[key] = value
        return decrypted_data

