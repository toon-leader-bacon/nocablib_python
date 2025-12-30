"""
Unit tests for NocabMT (Mersenne Twister implementation).
Focus on serialization and deterministic behavior.
"""

import unittest
import inspect
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from NocabRNG.NocabMT import NocabMT


RNG_DRAW_COUNT = 1000


def get_test_seed() -> int:
    """Get a deterministic seed based on the calling test function name"""
    frame = inspect.currentframe()
    if frame and frame.f_back:
        test_name = frame.f_back.f_code.co_name
        return hash(test_name) & 0x7FFFFFFF  # Keep positive
    return 12345


class TestNocabMT(unittest.TestCase):
    """Test cases for NocabMT class"""
    
    def test_basic_initialization(self):
        """Test that NocabMT initializes correctly with a seed"""
        seed = get_test_seed()
        rng = NocabMT(seed)
        self.assertIsNotNone(rng)
        self.assertEqual(len(rng.mt_state), 624)
    
    def test_deterministic_generation(self):
        """Test that same seed produces same sequence"""
        seed = get_test_seed()
        rng1 = NocabMT(seed)
        rng2 = NocabMT(seed)
        
        for _ in range(RNG_DRAW_COUNT):
            val1 = rng1.extract_number()
            val2 = rng2.extract_number()
            self.assertEqual(val1, val2, "Same seed should produce identical sequences")
    
    def test_serialization_basic(self):
        """Test basic serialization and deserialization"""
        seed = get_test_seed()
        rng = NocabMT(seed)
        
        # Generate some numbers to advance state
        for _ in range(100):
            rng.extract_number()
        
        # Serialize
        json_data = rng.to_json()
        
        # Verify JSON structure
        self.assertIn("type", json_data)
        self.assertEqual(json_data["type"], "NocabMT")
        self.assertIn("index", json_data)
        self.assertIn("mt", json_data)
        self.assertEqual(len(json_data["mt"]), 624)
    
    def test_serialization_produces_same_sequence(self):
        """
        CRITICAL TEST: After serialization/deserialization, 
        the RNG should produce the exact same sequence
        """
        seed = get_test_seed()
        rng1 = NocabMT(seed)
        
        # Generate some numbers to advance state
        for _ in range(250):
            rng1.extract_number()
        
        # Serialize and deserialize
        json_data = rng1.to_json()
        rng2 = NocabMT.from_dict(json_data)
        
        # Both should now produce identical sequences
        for i in range(RNG_DRAW_COUNT):
            val1 = rng1.extract_number()
            val2 = rng2.extract_number()
            self.assertEqual(val1, val2, 
                           f"Deserialized RNG diverged at draw {i}")
    
    def test_serialization_at_different_states(self):
        """Test serialization works at various points in the RNG lifecycle"""
        seed = get_test_seed()
        
        # Test at initial state
        rng_initial = NocabMT(seed)
        json_initial = rng_initial.to_json()
        rng_loaded = NocabMT.from_dict(json_initial)
        self.assertEqual(rng_initial.extract_number(), rng_loaded.extract_number())
        
        # Test after twist (624+ draws)
        rng_twisted = NocabMT(seed)
        for _ in range(700):
            rng_twisted.extract_number()
        json_twisted = rng_twisted.to_json()
        rng_loaded2 = NocabMT.from_dict(json_twisted)
        
        for _ in range(100):
            self.assertEqual(rng_twisted.extract_number(), rng_loaded2.extract_number())
    
    def test_output_range(self):
        """Test that generated numbers are in valid uint32 range"""
        seed = get_test_seed()
        rng = NocabMT(seed)
        
        for _ in range(RNG_DRAW_COUNT):
            val = rng.extract_number()
            self.assertGreaterEqual(val, 0, "Value should be >= 0")
            self.assertLessEqual(val, NocabMT.UNSIGNED_MAX_POSSIBLE_VALUE, 
                               "Value should be <= 2^32-1")
    
    def test_different_seeds_produce_different_sequences(self):
        """Test that different seeds produce different sequences"""
        seed1 = get_test_seed()
        seed2 = seed1 + 1
        
        rng1 = NocabMT(seed1)
        rng2 = NocabMT(seed2)
        
        # Check that sequences diverge
        differences = 0
        for _ in range(100):
            if rng1.extract_number() != rng2.extract_number():
                differences += 1
        
        self.assertGreater(differences, 90, 
                          "Different seeds should produce mostly different values")
    
    def test_twist_functionality(self):
        """Test that twist occurs after 624 draws"""
        seed = get_test_seed()
        rng = NocabMT(seed)
        
        # Initial index should be 624 (triggers immediate twist)
        self.assertEqual(rng.index, 624)
        
        # After one draw, index should be 1 (twist occurred, then incremented)
        rng.extract_number()
        self.assertEqual(rng.index, 1)
        
        # After 623 more draws, index should be 624
        for _ in range(623):
            rng.extract_number()
        self.assertEqual(rng.index, 624)
    
    def test_multiple_serialization_cycles(self):
        """Test multiple serialize/deserialize cycles maintain consistency"""
        seed = get_test_seed()
        rng = NocabMT(seed)
        
        # Generate reference sequence
        reference_values = []
        for _ in range(50):
            rng.extract_number()  # Advance state
        for _ in range(100):
            reference_values.append(rng.extract_number())
        
        # Now test with serialization cycles
        rng2 = NocabMT(seed)
        for _ in range(50):
            rng2.extract_number()
        
        # Serialize/deserialize 3 times
        for cycle in range(3):
            json_data = rng2.to_json()
            rng2 = NocabMT.from_dict(json_data)
        
        # Should still match reference
        for i, ref_val in enumerate(reference_values):
            val = rng2.extract_number()
            self.assertEqual(val, ref_val, 
                           f"Value diverged at position {i} after {cycle+1} cycles")
    
    def test_json_type_validation(self):
        """Test that loading invalid JSON type raises error"""
        seed = get_test_seed()
        rng = NocabMT(seed)
        
        json_data = rng.to_json()
        json_data["type"] = "InvalidType"
        
        with self.assertRaises(ValueError):
            NocabMT.from_dict(json_data)


if __name__ == '__main__':
    unittest.main()

