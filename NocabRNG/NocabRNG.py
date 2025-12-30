from typing import List, TypeVar, Optional, Dict, Any, Set, Iterator
import math
import time
import hashlib
from .NocabMT import NocabMT


T = TypeVar('T')


class NocabRNG:
    """
    Random Number Generator wrapper around NocabMT (Mersenne Twister).
    Provides various convenience methods for generating random values.
    """
    
    _default_rng: Optional['NocabRNG'] = None
    
    @classmethod
    def new_rng(cls) -> 'NocabRNG':
        """
        Warning: generating a new RNG object is expensive and slow.
        Recommended is to store the returned RNG object and use.
        
        Returns:
            New RNG instance seeded with current time
        """
        return cls(int(time.time() * 1000000))
    
    @classmethod
    def default_rng(cls) -> 'NocabRNG':
        """
        NOTE: The default_rng uses the same seed every time. So the order
        of generated numbers will not change between program runs.
        
        Returns:
            Singleton default RNG instance
        """
        if cls._default_rng is None:
            cls._default_rng = cls(5489)  # Default seed certified random according to Wikipedia
        return cls._default_rng
    
    def __init__(self, seed: int = 5489):
        """
        Initialize the RNG with a seed.
        
        Args:
            seed: Integer, string, or object to use as seed
        """
        if isinstance(seed, str):
            seed = hash(seed) & 0x7FFFFFFF  # Keep it positive
        elif not isinstance(seed, int):
            seed = hash(seed) & 0x7FFFFFFF
        
        self.my_rng = NocabMT(seed)
        
        # If two NocabRNG objects are created with the same seed, they will have the
        # same NocabName. This is not desirable (I want the ability to have multiple RNGs with the same seed).
        # So using the current time as a unique identifier is a workaround.
        name = self.generate_uuid() + str(int(time.time() * 1000000))
        self.nocab_name = name
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NocabRNG':
        """
        Create a NocabRNG instance from a dictionary (for deserialization).
        
        Args:
            data: Dictionary containing serialized state
            
        Returns:
            New NocabRNG instance with loaded state
        """
        instance = cls.__new__(cls)
        instance.load_json(data)
        return instance
    
    @property
    def nocab_name_property(self) -> str:
        """Get the unique name for this RNG instance"""
        return self.nocab_name
    
    # Value extraction
    
    def generate_uint(self) -> int:
        """Generate an unsigned 32-bit integer"""
        return self.my_rng.extract_number()
    
    def generate_int(self, low: int, high: int, low_inclusive: bool = True, high_inclusive: bool = True) -> int:
        """
        Generates a random int within the provided range of [low, high]. The default low and high
        values are inclusive in the range, meaning they are possible values to be returned.
        
        If low == high, then low_inclusive and high_inclusive must both be true. Otherwise an error is thrown.
        
        If low + 1 == high, then at least one of the of the inclusive parameters must be true. Else error.
        
        Args:
            low: Lower bound
            high: Upper bound
            low_inclusive: Whether low is included in range (default: True)
            high_inclusive: Whether high is included in range (default: True)
            
        Returns:
            Random integer in specified range
        """
        if low > high:
            err_msg = (f"Invalid range provided low={low}, high={high}. Swapping now. "
                      f"There may be some unexpected behavior relating to range inclusiveness.")
            print(err_msg)
            low, high = high, low
        
        # Check for invalid ranges like (4, 5)
        # IE: Pick an int between 4 and 5 that is not 4 nor 5 => invalid
        delta = high - low
        low_delta = 0 if low_inclusive else 1
        high_delta = 0 if high_inclusive else 1
        
        if delta < (low_delta + high_delta):
            raise ValueError(
                f"Invalid random int range. Low={low}  high={high}  "
                f"low_inclusive={low_inclusive}  high_inclusive={high_inclusive}"
            )
        
        return self._generate_int_internal(low + low_delta, (high + 1) - high_delta)  # high+1 because _generate_int_internal is high-exclusive
    
    def _generate_int_internal(self, low: int, high: int) -> int:
        """
        Please use the safe public generate_int(...) function.
        Generates an int in the range [low, high). That is, low inclusive, but high exclusive.
        
        If low == high, then that value is returned.
        
        Note: low > high is UNDEFINED BEHAVIOR.
        
        Args:
            low: Lower bound (inclusive)
            high: Upper bound (exclusive)
            
        Returns:
            Random integer in range [low, high)
        """
        if low == high:
            return low
        return low + int(math.floor((self.my_rng.extract_number() / NocabMT.MAX_POSSIBLE_VALUE_PLUS_ONE) * (high - low)))
    
    def generate_float(self, low: float, high: float, low_inclusive: bool = True, high_inclusive: bool = True) -> float:
        """
        Generate a random float in the specified range.
        
        Args:
            low: Lower bound
            high: Upper bound
            low_inclusive: Whether low is included in range (default: True)
            high_inclusive: Whether high is included in range (default: True)
            
        Returns:
            Random float in specified range
        """
        if low > high:
            err_msg = (f"Invalid range provided low={low}, high={high}. Swapping now. "
                      f"There may be some unexpected behavior relating to range inclusiveness.")
            print(err_msg)
            low, high = high, low
        
        random_number = float(self.my_rng.extract_number())
        if not low_inclusive and (random_number == 0.0):
            random_number = 1e-45  # Approximate float epsilon
        
        denominator = NocabMT.UNSIGNED_MAX_POSSIBLE_VALUE if high_inclusive else NocabMT.MAX_POSSIBLE_VALUE_PLUS_ONE
        return low + ((random_number / denominator) * (high - low))
    
    def generate_double(self, low: float, high: float, low_inclusive: bool = True, high_inclusive: bool = False) -> float:
        """
        Generate a random double (float) in the specified range.
        
        Args:
            low: Lower bound
            high: Upper bound
            low_inclusive: Whether low is included in range (default: True)
            high_inclusive: Whether high is included in range (default: False)
            
        Returns:
            Random float in specified range
        """
        if low > high:
            err_msg = (f"Invalid range provided low={low}, high={high}. Swapping now. "
                      f"There may be some unexpected behavior relating to range inclusiveness.")
            print(err_msg)
            low, high = high, low
        
        random_number = float(self.my_rng.extract_number())
        if not low_inclusive and (random_number == 0.0):
            random_number = 2.2250738585072014e-308  # Approximate double epsilon
        
        denominator = NocabMT.UNSIGNED_MAX_POSSIBLE_VALUE if high_inclusive else NocabMT.MAX_POSSIBLE_VALUE_PLUS_ONE
        return low + ((random_number / denominator) * (high - low))
    
    def generate_bool(self) -> bool:
        """Generate a random boolean value"""
        return (self.my_rng.extract_number() % 2) == 1
    
    def generate_byte_list(self, number_of_bytes: int) -> List[int]:
        """
        Returns a list of randomly generated bytes. The length of the list
        is the absolute value of the input parameter number_of_bytes.
        
        Args:
            number_of_bytes: Number of bytes to generate
            
        Returns:
            List of random bytes (0-255)
        """
        number_of_bytes = abs(number_of_bytes)
        result: List[int] = []
        total_uints = number_of_bytes // 4  # How many full uint32 to add to result
        remainder_bytes = number_of_bytes % 4  # How many remainder bytes to add to result
        
        # Generate 'total_uints' number of uints, and add all those bytes to the result.
        for i in range(total_uints):
            uint_val = self.my_rng.extract_number()
            result.append(uint_val & 0xFF)
            result.append((uint_val >> 8) & 0xFF)
            result.append((uint_val >> 16) & 0xFF)
            result.append((uint_val >> 24) & 0xFF)
        
        if remainder_bytes == 0:
            return result
        
        # Add in the remainder bytes
        uint_val = self.my_rng.extract_number()
        for i in range(remainder_bytes):
            result.append((uint_val >> (i * 8)) & 0xFF)
        
        return result
    
    def generate_uuid(self, number_of_bytes: int = 16) -> str:
        """
        The method returns a hexadecimal string. Every two characters is one byte
        in hex code. Every byte is randomly generated. The input parameter
        number_of_bytes represents how many bytes are used to construct the UUID.
        Providing a number_of_bytes that is divisible by 4 is recommended.
        
        Example output:
        Default 16 number_of_bytes -> "5cbb91d0f69eae22eefae1e7791fc3d5"
        (number_of_bytes = 1) -> "2c"
        
        Args:
            number_of_bytes: Number of bytes to use (default: 16)
            
        Returns:
            Hexadecimal string representation
        """
        bytes_list = self.generate_byte_list(number_of_bytes)
        return ''.join(f'{b:02x}' for b in bytes_list)
    
    # Dice
    
    @property
    def d100(self) -> int:
        """Roll a 100-sided die (1-100)"""
        return self._generate_int_internal(1, 101)
    
    @property
    def d20(self) -> int:
        """Roll a 20-sided die (1-20)"""
        return self._generate_int_internal(1, 21)
    
    @property
    def d12(self) -> int:
        """Roll a 12-sided die (1-12)"""
        return self._generate_int_internal(1, 13)
    
    @property
    def d6(self) -> int:
        """Roll a 6-sided die (1-6)"""
        return self._generate_int_internal(1, 7)
    
    @property
    def d4(self) -> int:
        """Roll a 4-sided die (1-4)"""
        return self._generate_int_internal(1, 5)
    
    def roll_n_sided_die(self, n: int) -> int:
        """
        Roll an n-sided die.
        
        Args:
            n: Number of sides
            
        Returns:
            Random value from 1 to n (inclusive)
        """
        return self._generate_int_internal(1, max(1, n + 1))
    
    # Between 0 and 1
    
    @property
    def unit_float(self) -> float:
        """Generate a float between 0 and 1 (inclusive)"""
        return self.generate_float(0.0, 1.0, True, True)
    
    @property
    def unit_double(self) -> float:
        """Generate a double between 0 and 1 (inclusive)"""
        return self.generate_double(0.0, 1.0, True, True)
    
    # Collection Based
    
    def random_elem(self, lst: List[T]) -> T:
        """
        Select and return a random element in the provided list.
        If list.Count == 0 an error is thrown.
        
        Args:
            lst: List to select from
            
        Returns:
            Random element from the list
            
        Raises:
            ValueError: If list is empty
        """
        if len(lst) == 0:
            raise ValueError("Can NOT pull a random elem from a list with 0 elements.")
        return lst[self.random_index(len(lst))]
    
    def random_elem_set(self, elems: Set[T]) -> T:
        """
        @brief Select and returns a random element in the provided set.
        This is a O(n) function, using a List is recommended.
        If a set of size 0 is provided an error is thrown.
        
        Args:
            elems: Set to select from
            
        Returns:
            Random element from the set
            
        Raises:
            ValueError: If set is empty
        """
        if len(elems) == 0:
            raise ValueError("Can NOT pull a random elem from a set with 0 elements.")
        
        rand_index = self.random_index(len(elems))
        
        for elem in elems:
            if rand_index <= 0:
                return elem
            rand_index -= 1
        
        raise Exception(f"Something has gone wrong! RandIndex = {rand_index}, elems.Count = {len(elems)}")
    
    def random_elem_iterator(self, iterator: Iterator[T]) -> T:
        """
        @brief Select and returns a random element in the provided enumerable.
        This is a O(n) function, using a List is recommended.
        If an enum of size 0 is provided an error is thrown.
        
        Args:
            iterator: Iterator to select from
            
        Returns:
            Random element from the iterator
            
        Raises:
            ValueError: If iterator is empty
        """
        # Convert the iterator into a List
        lst = list(iterator)
        
        # Validate the list
        if len(lst) == 0:
            error_msg = "Can NOT pull a random elem for a collection with 0 elements!"
            raise ValueError(error_msg)
        
        # Use the list to pull a random element.
        return self.random_elem(lst)
    
    def random_index(self, count: int) -> int:
        """
        Generate a random index for a collection of given size.
        
        Args:
            count: Size of collection
            
        Returns:
            Random index in range [0, count)
            
        Raises:
            ValueError: If count <= 0
        """
        if count <= 0:
            raise ValueError(f"Must provide a positive count to random_index(). Count {count}")
        return self._generate_int_internal(0, count)
    
    # TODO: Consider using % Count instead of generating a number between [0, count)
    #       It might be faster, but not sure if it's worth it.
    
    def shuffle_in_place(self, to_be_shuffled: List[T]) -> None:
        """
        Fisher-Yates shuffle. Details found here:
        https://en.wikipedia.org/wiki/Fisher%E2%80%93Yates_shuffle
        
        In summary, the list will be partitioned into two parts.
        Everything to the left of (less than) the separator is the "shuffled"
        list. A random index will be chosen in the range [separator, count).
        The value at the random index will be swapped with the value at the
        separator. Then the separator will increment.
        
        Args:
            to_be_shuffled: List to shuffle in place
        """
        for separator in range(len(to_be_shuffled)):
            j = self.generate_int(separator, len(to_be_shuffled), True, False)
            
            # Swap
            to_be_shuffled[j], to_be_shuffled[separator] = to_be_shuffled[separator], to_be_shuffled[j]
    
    def shuffle_new_list(self, shuffle_input: List[T]) -> List[T]:
        """
        Create a shuffled copy of the input list.
        
        Args:
            shuffle_input: List to shuffle
            
        Returns:
            New shuffled list
        """
        result = shuffle_input.copy()
        self.shuffle_in_place(result)
        return result
    
    # Saving
    
    JSON_TYPE: str = "NocabRNG"  # version 1.0
    
    def my_json_type(self) -> str:
        """Return the JSON type identifier for this class"""
        return self.JSON_TYPE
    
    def to_json(self) -> Dict[str, Any]:
        """
        Serialize the RNG state to a dictionary.
        
        Returns:
            Dictionary containing the complete state
        """
        return {
            "type": self.JSON_TYPE,
            "rng": self.my_rng.to_json(),
            "NocabName": self.nocab_name
        }
    
    def load_json(self, jo: Dict[str, Any]) -> None:
        """
        Deserialize the RNG state from a dictionary.
        
        Args:
            jo: Dictionary containing serialized state
            
        Raises:
            ValueError: If the JSON type doesn't match
        """
        if jo.get("type") != self.JSON_TYPE:
            raise ValueError(f"Invalid JSON type. Expected {self.JSON_TYPE}, got {jo.get('type')}")
        
        self.my_rng = NocabMT.from_dict(jo["rng"])
        self.nocab_name = jo["NocabName"]

