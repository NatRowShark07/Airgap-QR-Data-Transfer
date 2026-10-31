"""
test_aqrdt.py - Comprehensive Unit Test Suite for Airgapped QR Data Transfer (AQRDT v2.0)
Tests encryption, decryption, lossless compression, auth signatures, packets, and ARQ.
"""

import unittest
import os
import zlib
import hashlib
import tempfile
import importlib.util

# Dynamic import of Duplex AQRDT.py
script_dir = os.path.dirname(os.path.abspath(__file__))
aqrdt_path = os.path.join(script_dir, "Duplex AQRDT.py")
spec = importlib.util.spec_from_file_location("duplex_aqrdt", aqrdt_path)
aqrdt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(aqrdt)


class TestAQRDTv2(unittest.TestCase):

    def setUp(self):
        self.test_user = "Nathaniel"
        self.test_pass = "AirgapSecurePass2026!"

    def test_auth_signature_and_verification(self):
        # Generate Auth QR payload
        payload = aqrdt.generate_auth_qr_payload(self.test_user, self.test_pass)
        self.assertTrue(payload.startswith("AUTH|AQRDT|v2|Nathaniel|"))

        # Verify correct credentials
        valid, user = aqrdt.verify_auth_payload(payload, self.test_user, self.test_pass)
        self.assertTrue(valid)
        self.assertEqual(user, self.test_user)

        # Verify wrong password rejects
        invalid, _ = aqrdt.verify_auth_payload(payload, self.test_user, "WrongPassword!")
        self.assertFalse(invalid)

    def test_lossless_compression_and_sha256_encryption(self):
        original_data = b"Secret payload data for airgapped transfer testing." * 25
        orig_hash = hashlib.sha256(original_data).hexdigest()

        # Pack and Encrypt
        container, sha_hex, is_compressed, ratio = aqrdt.pack_and_encrypt_file(
            original_data, self.test_user, self.test_pass
        )

        self.assertEqual(sha_hex, orig_hash)
        self.assertTrue(is_compressed)
        self.assertGreater(ratio, 50.0)  # Significant lossless compression ratio
        self.assertTrue(container.startswith(aqrdt.MAGIC_CONTAINER_V2))

        # Decrypt and Unpack
        decrypted_bytes, recovered_sha = aqrdt.decrypt_and_unpack_container(
            container, self.test_user, self.test_pass
        )

        self.assertEqual(decrypted_bytes, original_data)
        self.assertEqual(recovered_sha, orig_hash)

    def test_tampered_container_and_wrong_password(self):
        original_data = b"Sensitive classified document." * 10
        container, _, _, _ = aqrdt.pack_and_encrypt_file(original_data, self.test_user, self.test_pass)

        # Attempt decryption with wrong password
        with self.assertRaises(ValueError) as ctx:
            aqrdt.decrypt_and_unpack_container(container, self.test_user, "IncorrectPassword")
        self.assertIn("Decryption failed", str(ctx.exception))

        # Tampered ciphertext
        tampered_container = bytearray(container)
        tampered_container[-1] ^= 0xFF
        with self.assertRaises(ValueError):
            aqrdt.decrypt_and_unpack_container(bytes(tampered_container), self.test_user, self.test_pass)

    def test_range_compression_and_decompression(self):
        indices = [0, 1, 2, 3, 5, 7, 8, 9, 12, 13, 14, 20]
        compressed = aqrdt.compress_indices(indices)
        self.assertEqual(compressed, "0-3,5,7-9,12-14,20")

        decompressed = aqrdt.decompress_indices(compressed)
        self.assertEqual(decompressed, indices)

        # Edge cases
        self.assertEqual(aqrdt.compress_indices([]), "")
        self.assertEqual(aqrdt.compress_indices([7]), "7")
        self.assertEqual(aqrdt.decompress_indices(""), [])
        self.assertEqual(aqrdt.decompress_indices("7"), [7])

    def test_packet_creation_and_crc_validation(self):
        payload = b"Packet payload bytes 12345"
        pkt_str = aqrdt.create_data_packet("sample.txt", 2, 10, payload)

        parsed = aqrdt.parse_data_packet(pkt_str)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["filename"], "sample.txt")
        self.assertEqual(parsed["idx"], 2)
        self.assertEqual(parsed["total"], 10)
        self.assertEqual(parsed["chunk_bytes"], payload)

        # Corrupt CRC
        corrupted_pkt = pkt_str[:-4] + "AAAA"
        self.assertIsNone(aqrdt.parse_data_packet(corrupted_pkt))

    def test_terminal_qr_rendering(self):
        qr_ascii = aqrdt.render_terminal_qr("AQRDT_TEST_PAYLOAD", invert=True, double_width=True)
        self.assertIn("██", qr_ascii)
        self.assertIn("  ", qr_ascii)
        self.assertGreater(len(qr_ascii.split("\n")), 15)

    def test_clean_path_input(self):
        self.assertEqual(
            aqrdt.clean_path_input("& 'C:\\Users\\Nathaniel\\Data.txt'"),
            "C:\\Users\\Nathaniel\\Data.txt"
        )
        self.assertEqual(
            aqrdt.clean_path_input('"./received_files/output.bin"'),
            "./received_files/output.bin"
        )


if __name__ == "__main__":
    unittest.main()
