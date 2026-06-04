import os
import base64
import hashlib
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from src.core.logger import get_logger

CURRENT_USER_SIGNATURE_KEY_ENV = "USER_SIGNATURE_PRIVATE_KEY"
# Intentionally keeps the requested suffix spelling for deployment compatibility.
PREVIOUS_USER_SIGNATURE_KEY_ENV = "USER_SIGNATURE_PRIVATE_KEY_PREVIUS"


class Cryptography:
    def __init__(self):
        self.logger = get_logger("core:crypto")
        self.current_key = self._load_key(CURRENT_USER_SIGNATURE_KEY_ENV, required=True)
        self.previous_key = self._load_key(PREVIOUS_USER_SIGNATURE_KEY_ENV, required=False)
        self.block_size = algorithms.AES.block_size // 8  # typically 16 bytes

    def _load_key(self, env_name: str, *, required: bool) -> bytes | None:
        key_b64 = os.getenv(env_name)
        if not key_b64:
            if required:
                self.logger.error("Missing %s environment variable", env_name)
                raise Exception(f"Missing {env_name} environment variable")
            return None

        try:
            key = base64.b64decode(key_b64)
        except Exception as exc:
            self.logger.error("Failed to decode %s: %s", env_name, exc)
            raise

        if len(key) != 32:
            self.logger.error("%s must decode to exactly 32 bytes", env_name)
            raise ValueError(f"{env_name} must decode to exactly 32 bytes")

        return key

    def encrypt(self, data: str) -> bytes:
        try:
            iv = os.urandom(self.block_size)
            cipher = Cipher(algorithms.AES(self.current_key), modes.CBC(iv), backend=default_backend())
            encryptor = cipher.encryptor()

            # Apply PKCS7 padding
            padder = padding.PKCS7(algorithms.AES.block_size).padder()
            padded_data = padder.update(data.encode()) + padder.finalize()
            ciphertext = encryptor.update(padded_data) + encryptor.finalize()

            # Return IV concatenated with ciphertext
            return iv + ciphertext
        except Exception as e:
            self.logger.error(f"Error encrypting data: {e}")
            raise

    def _decrypt_with_key(self, encrypted: bytes, key: bytes) -> str:
        iv = encrypted[:self.block_size]
        ciphertext = encrypted[self.block_size:]
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        data = unpadder.update(padded_data) + unpadder.finalize()
        return data.decode()

    def decrypt(self, encrypted: bytes) -> str:
        last_error = None

        try:
            return self._decrypt_with_key(encrypted, self.current_key)
        except Exception as exc:
            last_error = exc
            self.logger.warning("Error decrypting data with %s", CURRENT_USER_SIGNATURE_KEY_ENV)

        if self.previous_key is not None:
            try:
                plaintext = self._decrypt_with_key(encrypted, self.previous_key)
                self.logger.info("Decrypted data with fallback key %s", PREVIOUS_USER_SIGNATURE_KEY_ENV)
                return plaintext
            except Exception as exc:
                last_error = exc
                self.logger.warning("Error decrypting data with %s", PREVIOUS_USER_SIGNATURE_KEY_ENV)

        if last_error is not None:
            self.logger.error("Error decrypting data: %s", last_error)
            raise last_error
        raise ValueError("No decryption key available")

    def url_safe_base64_encode(self, value: bytes) -> str:
        try:
            encoded = base64.b64encode(value).decode()
            # Replace unsafe characters: +, =, /  -> -, _, ~
            return encoded.replace('+', '-').replace('=', '_').replace('/', '~')
        except Exception as e:
            self.logger.error(f"Error encoding data: {e}")
            raise

    def url_safe_base64_decode(self, value: str) -> bytes:
        try:
            # Reverse the replacements
            decoded_str = value.replace('-', '+').replace('_', '=').replace('~', '/')
            return base64.b64decode(decoded_str)
        except Exception as e:
            self.logger.error(f"Error decoding data: {e}")
            raise

    def hash_token(self, token_base: str) -> str:
        try:
            return hashlib.sha3_224(token_base.encode()).hexdigest()
        except Exception as e:
            self.logger.error(f"Error hashing token: {e}")
            raise
