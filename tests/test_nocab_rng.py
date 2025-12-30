"""
Unit tests for NocabRNG (high-level RNG wrapper).
Focus on serialization, deterministic behavior, and range validation.
"""

import unittest
import inspect
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from NocabRNG.NocabRNG import NocabRNG


RNG_DRAW_COUNT = 1000


def get_test_seed() -> int:
    """Get a deterministic seed based on the calling test function name"""
    frame = inspect.currentframe()
    if frame and frame.f_back:
        test_name = frame.f_back.f_code.co_name
        return hash(test_name) & 0x7FFFFFFF  # Keep positive
    return 12345


class TestNocabRNG(unittest.TestCase):
    """Test cases for NocabRNG class"""
    
    def test_basic_initialization(self):
        """Test that NocabRNG initializes correctly"""
        seed = get_test_seed()
        rng = NocabRNG(seed)
        self.assertIsNotNone(rng)
        self.assertIsNotNone(rng.my_rng)
        self.assertIsNotNone(rng.nocab_name)
    
    def test_deterministic_uint_generation(self):
        """Test that same seed produces same uint sequence"""
        seed = get_test_seed()
        rng1 = NocabRNG(seed)
        rng2 = NocabRNG(seed)
        
        for _ in range(RNG_DRAW_COUNT):
            val1 = rng1.generate_uint()
            val2 = rng2.generate_uint()
            self.assertEqual(val1, val2, "Same seed should produce identical sequences")
    
    def test_serialization_produces_same_sequence(self):
        """
        CRITICAL TEST: After serialization/deserialization,
        the RNG should produce the exact same sequence
        """
        seed = get_test_seed()
        rng1 = NocabRNG(seed)
        
        # Generate some numbers to advance state
        for _ in range(250):
            rng1.generate_uint()
        
        # Serialize and deserialize
        json_data = rng1.to_json()
        rng2 = NocabRNG.from_dict(json_data)
        
        # Both should now produce identical sequences
        for i in range(RNG_DRAW_COUNT):
            val1 = rng1.generate_uint()
            val2 = rng2.generate_uint()
            self.assertEqual(val1, val2,
                           f"Deserialized RNG diverged at draw {i}")
    
    def test_serialization_preserves_complex_operations(self):
        """Test that serialization works with various RNG operations"""
        seed = get_test_seed()
        rng1 = NocabRNG(seed)
        
        # Perform various operations
        for _ in range(50):
            rng1.generate_int(1, 100)
            rng1.generate_float(0.0, 1.0)
            rng1.generate_bool()
        
        # Serialize
        json_data = rng1.to_json()
        rng2 = NocabRNG.from_dict(json_data)
        
        # Continue with same operations - should match
        for _ in range(100):
            self.assertEqual(rng1.generate_int(1, 100), rng2.generate_int(1, 100))
            self.assertEqual(rng1.generate_float(0.0, 1.0), rng2.generate_float(0.0, 1.0))
            self.assertEqual(rng1.generate_bool(), rng2.generate_bool())
    
    def test_generate_int_range(self):
        """Test that generate_int produces values in correct range"""
        seed = get_test_seed()
        rng = NocabRNG(seed)
        
        low, high = 10, 50
        for _ in range(RNG_DRAW_COUNT):
            val = rng.generate_int(low, high)
            self.assertGreaterEqual(val, low, f"Value {val} below minimum {low}")
            self.assertLessEqual(val, high, f"Value {val} above maximum {high}")
    
    def test_generate_int_inclusive_exclusive(self):
        """Test inclusive/exclusive bounds for generate_int"""
        seed = get_test_seed()
        
        # Test [10, 20] inclusive
        rng1 = NocabRNG(seed)
        values_inclusive = [rng1.generate_int(10, 20, True, True) for _ in range(RNG_DRAW_COUNT)]
        self.assertIn(10, values_inclusive, "10 should appear with inclusive bounds")
        self.assertIn(20, values_inclusive, "20 should appear with inclusive bounds")
        
        # Test (10, 20) exclusive
        rng2 = NocabRNG(seed + 1)
        values_exclusive = [rng2.generate_int(10, 20, False, False) for _ in range(RNG_DRAW_COUNT)]
        self.assertNotIn(10, values_exclusive, "10 should not appear with exclusive bounds")
        self.assertNotIn(20, values_exclusive, "20 should not appear with exclusive bounds")
        self.assertTrue(all(11 <= v <= 19 for v in values_exclusive))
    
    def test_generate_float_range(self):
        """Test that generate_float produces values in correct range"""
        seed = get_test_seed()
        rng = NocabRNG(seed)
        
        low, high = 5.0, 15.0
        for _ in range(RNG_DRAW_COUNT):
            val = rng.generate_float(low, high)
            self.assertGreaterEqual(val, low, f"Value {val} below minimum {low}")
            self.assertLessEqual(val, high, f"Value {val} above maximum {high}")
    
    def test_generate_double_range(self):
        """Test that generate_double produces values in correct range"""
        seed = get_test_seed()
        rng = NocabRNG(seed)
        
        # Note: generate_double defaults to high_inclusive=False, so range is [low, high)
        low, high = -10.0, 10.0
        for _ in range(RNG_DRAW_COUNT):
            val = rng.generate_double(low, high)
            self.assertGreaterEqual(val, low, f"Value {val} below minimum {low}")
            self.assertLess(val, high, f"Value {val} should be < {high} (exclusive)")
    
    def test_generate_bool_distribution(self):
        """Test that generate_bool produces reasonable distribution"""
        seed = get_test_seed()
        rng = NocabRNG(seed)
        
        true_count = sum(1 for _ in range(RNG_DRAW_COUNT) if rng.generate_bool())
        false_count = RNG_DRAW_COUNT - true_count
        
        # Should be roughly 50/50, allow 40-60% range
        self.assertGreater(true_count, RNG_DRAW_COUNT * 0.4)
        self.assertLess(true_count, RNG_DRAW_COUNT * 0.6)
    
    def test_dice_rolls_range(self):
        """Test that dice rolls produce values in correct ranges"""
        seed = get_test_seed()
        rng = NocabRNG(seed)
        
        # Test d6
        for _ in range(RNG_DRAW_COUNT):
            val = rng.d6
            self.assertGreaterEqual(val, 1)
            self.assertLessEqual(val, 6)
        
        # Test d20
        for _ in range(RNG_DRAW_COUNT):
            val = rng.d20
            self.assertGreaterEqual(val, 1)
            self.assertLessEqual(val, 20)
        
        # Test d100
        for _ in range(RNG_DRAW_COUNT):
            val = rng.d100
            self.assertGreaterEqual(val, 1)
            self.assertLessEqual(val, 100)
    
    def test_roll_n_sided_die(self):
        """Test custom n-sided die"""
        seed = get_test_seed()
        rng = NocabRNG(seed)
        
        n = 13
        for _ in range(RNG_DRAW_COUNT):
            val = rng.roll_n_sided_die(n)
            self.assertGreaterEqual(val, 1)
            self.assertLessEqual(val, n)
    
    def test_unit_float_range(self):
        """Test that unit_float produces values in [0, 1]"""
        seed = get_test_seed()
        rng = NocabRNG(seed)
        
        for _ in range(RNG_DRAW_COUNT):
            val = rng.unit_float
            self.assertGreaterEqual(val, 0.0)
            self.assertLessEqual(val, 1.0)
    
    def test_unit_double_range(self):
        """Test that unit_double produces values in [0, 1]"""
        seed = get_test_seed()
        rng = NocabRNG(seed)
        
        for _ in range(RNG_DRAW_COUNT):
            val = rng.unit_double
            self.assertGreaterEqual(val, 0.0)
            self.assertLessEqual(val, 1.0)
    
    def test_generate_byte_list(self):
        """Test byte list generation"""
        seed = get_test_seed()
        rng = NocabRNG(seed)
        
        # Test various sizes
        for size in [1, 4, 16, 17, 100]:
            bytes_list = rng.generate_byte_list(size)
            self.assertEqual(len(bytes_list), size)
            for byte in bytes_list:
                self.assertGreaterEqual(byte, 0)
                self.assertLessEqual(byte, 255)
    
    def test_generate_uuid(self):
        """Test UUID generation"""
        seed = get_test_seed()
        rng = NocabRNG(seed)
        
        # Default 16 bytes = 32 hex chars
        uuid = rng.generate_uuid()
        self.assertEqual(len(uuid), 32)
        self.assertTrue(all(c in '0123456789abcdef' for c in uuid))
        
        # Custom size
        uuid_small = rng.generate_uuid(4)
        self.assertEqual(len(uuid_small), 8)
    
    def test_random_elem_list(self):
        """Test random element selection from list"""
        seed = get_test_seed()
        rng = NocabRNG(seed)
        
        test_list = [10, 20, 30, 40, 50]
        
        # All selected elements should be in the list
        for _ in range(100):
            elem = rng.random_elem(test_list)
            self.assertIn(elem, test_list)
        
        # Should eventually hit all elements (probabilistic)
        selected = set()
        for _ in range(RNG_DRAW_COUNT):
            selected.add(rng.random_elem(test_list))
        self.assertEqual(len(selected), len(test_list), 
                        "Should select all elements over many draws")
    
    def test_random_elem_empty_list_raises(self):
        """Test that random_elem raises error on empty list"""
        seed = get_test_seed()
        rng = NocabRNG(seed)
        
        with self.assertRaises(ValueError):
            rng.random_elem([])
    
    def test_random_elem_set(self):
        """Test random element selection from set"""
        seed = get_test_seed()
        rng = NocabRNG(seed)
        
        test_set = {10, 20, 30, 40, 50}
        
        for _ in range(100):
            elem = rng.random_elem_set(test_set)
            self.assertIn(elem, test_set)
    
    def test_random_index(self):
        """Test random index generation"""
        seed = get_test_seed()
        rng = NocabRNG(seed)
        
        count = 10
        for _ in range(RNG_DRAW_COUNT):
            idx = rng.random_index(count)
            self.assertGreaterEqual(idx, 0)
            self.assertLess(idx, count)
    
    def test_shuffle_in_place(self):
        """Test in-place shuffling"""
        seed = get_test_seed()
        rng = NocabRNG(seed)
        
        original = list(range(20))
        to_shuffle = original.copy()
        
        rng.shuffle_in_place(to_shuffle)
        
        # Should contain same elements
        self.assertEqual(sorted(to_shuffle), original)
        
        # Should be shuffled (very unlikely to be same order)
        self.assertNotEqual(to_shuffle, original)
    
    def test_shuffle_new_list(self):
        """Test shuffling with new list creation"""
        seed = get_test_seed()
        rng = NocabRNG(seed)
        
        original = list(range(20))
        shuffled = rng.shuffle_new_list(original)
        
        # Original should be unchanged
        self.assertEqual(original, list(range(20)))
        
        # Shuffled should contain same elements
        self.assertEqual(sorted(shuffled), original)
        
        # Should be shuffled
        self.assertNotEqual(shuffled, original)
    
    def test_shuffle_deterministic(self):
        """Test that shuffle is deterministic with same seed"""
        seed = get_test_seed()
        
        rng1 = NocabRNG(seed)
        list1 = list(range(50))
        rng1.shuffle_in_place(list1)
        
        rng2 = NocabRNG(seed)
        list2 = list(range(50))
        rng2.shuffle_in_place(list2)
        
        self.assertEqual(list1, list2, "Same seed should produce same shuffle")
    
    def test_shuffle_serialization(self):
        """Test that shuffle works correctly after serialization"""
        seed = get_test_seed()
        rng1 = NocabRNG(seed)
        
        # Shuffle a list
        list1 = list(range(20))
        rng1.shuffle_in_place(list1)
        
        # Serialize
        json_data = rng1.to_json()
        rng2 = NocabRNG.from_dict(json_data)
        
        # Both should shuffle identically going forward
        list2 = list(range(20))
        list3 = list(range(20))
        
        rng1.shuffle_in_place(list2)
        rng2.shuffle_in_place(list3)
        
        self.assertEqual(list2, list3)
    
    def test_multiple_serialization_cycles(self):
        """Test multiple serialize/deserialize cycles maintain consistency"""
        seed = get_test_seed()
        rng = NocabRNG(seed)
        
        # Generate reference sequence
        reference_values = []
        for _ in range(50):
            rng.generate_int(1, 1000)  # Advance state
        for _ in range(100):
            reference_values.append(rng.generate_int(1, 1000))
        
        # Now test with serialization cycles
        rng2 = NocabRNG(seed)
        for _ in range(50):
            rng2.generate_int(1, 1000)
        
        # Serialize/deserialize 5 times
        for _ in range(5):
            json_data = rng2.to_json()
            rng2 = NocabRNG.from_dict(json_data)
        
        # Should still match reference
        for i, ref_val in enumerate(reference_values):
            val = rng2.generate_int(1, 1000)
            self.assertEqual(val, ref_val,
                           f"Value diverged at position {i}")
    
    def test_string_seed(self):
        """Test initialization with string seed"""
        rng1 = NocabRNG("test_seed_string")
        rng2 = NocabRNG("test_seed_string")
        
        # Same string should produce same sequence
        for _ in range(100):
            self.assertEqual(rng1.generate_uint(), rng2.generate_uint())
    
    def test_default_rng_singleton(self):
        """Test that default_rng returns singleton"""
        rng1 = NocabRNG.default_rng()
        rng2 = NocabRNG.default_rng()
        
        # Should be same instance
        self.assertIs(rng1, rng2)
    
    def test_json_type_validation(self):
        """Test that loading invalid JSON type raises error"""
        seed = get_test_seed()
        rng = NocabRNG(seed)
        
        json_data = rng.to_json()
        json_data["type"] = "InvalidType"
        
        with self.assertRaises(ValueError):
            NocabRNG.from_dict(json_data)
    
    def test_invalid_range_raises_error(self):
        """Test that invalid ranges raise appropriate errors"""
        seed = get_test_seed()
        rng = NocabRNG(seed)
        
        # Test exclusive range with no valid values
        with self.assertRaises(ValueError):
            rng.generate_int(5, 5, False, False)
        
        with self.assertRaises(ValueError):
            rng.generate_int(5, 6, False, False)
    
    def test_serialization_json_structure(self):
        """Test that serialized JSON has correct structure"""
        seed = get_test_seed()
        rng = NocabRNG(seed)
        
        json_data = rng.to_json()
        
        # Check top-level structure
        self.assertIn("type", json_data)
        self.assertEqual(json_data["type"], "NocabRNG")
        self.assertIn("rng", json_data)
        self.assertIn("NocabName", json_data)
        
        # Check nested MT structure
        mt_data = json_data["rng"]
        self.assertIn("type", mt_data)
        self.assertEqual(mt_data["type"], "NocabMT")
        self.assertIn("index", mt_data)
        self.assertIn("mt", mt_data)


if __name__ == '__main__':
    unittest.main()

