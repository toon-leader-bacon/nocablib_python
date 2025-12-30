from typing import List, Dict, Any
import math


class NocabMT:
    """
    Mersenne Twister, following the pseudo code from Wikipedia.
    https://en.wikipedia.org/wiki/Mersenne_Twister
    
    Generates an unsigned int (32 bit) in the range between [0, (2^32) - 1] Or [0, 4,294,967,295]
    """
    
    UNSIGNED_MAX_POSSIBLE_VALUE: int = 4294967295  # (2^32) - 1
    MAX_POSSIBLE_VALUE_PLUS_ONE: float = 4294967296.0  # (2^32). Float is required because uint overflow
    
    # Constants
    _WORD_LENGTH: int = 32  # number of bits
    _STATE_LENGTH: int = 624  # degree of recurrence
    _M: int = 397  # middle word, an offset used in defining the series X.  1 <= m < n
    _R: int = 31  # separation point of one word, # bits of lower bitmask.  0 <= r <= w-1
    _A: int = 2567483615  # Coefficients of the rational normal form twist matrix
    
    _U: int = 11  # Tempering bit shift
    
    # private const uint d = 0xFFFFFFFF; // Un-used for 32 bit generation
    _S: int = 7  # Tempering bitshift
    _B: int = 0x9D2C5680  # Tempering mask
    _T: int = 15  # Tempering bitshift
    _C: int = 0xEFC60000  # Tempering mask
    _L: int = 18  # Tempering bitshift
    
    _F32: int = 1812433253
    _UPPER_MASK: int = 0b_1000_0000_0000_0000_0000_0000_0000_0000  # Most significant w-r bits
    _LOWER_MASK: int = 0b_0111_1111_1111_1111_1111_1111_1111_1111  # least significant r bits
    
    def __init__(self, seed: int = 5489):
        """
        Initialize the Mersenne Twister with a seed.
        
        Args:
            seed: Integer seed value (default: 5489)
        """
        # Create a length n array to store the generator state
        self.mt_state: List[int] = [0] * self._STATE_LENGTH
        self.index: int = self._STATE_LENGTH
        self._initialize_state(seed)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NocabMT':
        """
        Create a NocabMT instance from a dictionary (for deserialization).
        
        Args:
            data: Dictionary containing serialized state
            
        Returns:
            New NocabMT instance with loaded state
        """
        instance = cls.__new__(cls)
        instance.load_json(data)
        return instance
    
    def _initialize_state(self, seed: int) -> None:
        """Initialize the generator from a seed"""
        # Ensure seed is treated as unsigned 32-bit
        seed = seed & 0xFFFFFFFF
        self.mt_state[0] = seed
        
        for i in range(1, self._STATE_LENGTH):
            prev = self.mt_state[i - 1]
            self.mt_state[i] = (self._F32 * (prev ^ (prev >> (self._WORD_LENGTH - 2))) + i) & 0xFFFFFFFF
    
    def extract_number(self) -> int:
        """
        Extract a tempered value based on mt_state[index]
        calling twist() every n numbers
        
        Returns:
            Random unsigned 32-bit integer
        """
        if self.index >= self._STATE_LENGTH:
            self._twist()
        
        y = self.mt_state[self.index]
        self.index += 1
        
        # Tempering
        y ^= (y >> self._U)
        y ^= ((y << self._S) & self._B)
        y ^= ((y << self._T) & self._C)
        y ^= (y >> self._L)
        
        return y & 0xFFFFFFFF
    
    def _twist(self) -> None:
        """Generate the next n values from the series x_i"""
        for i in range(self._STATE_LENGTH):
            x = (self.mt_state[i] & self._UPPER_MASK) + (self.mt_state[(i + 1) % self._STATE_LENGTH] & self._LOWER_MASK)
            xA = x >> 1
            if (x % 2) == 1:
                # Lowest bit of x is 1
                xA = xA ^ self._A
            self.mt_state[i] = (self.mt_state[(i + self._M) % self._STATE_LENGTH] ^ xA) & 0xFFFFFFFF
        self.index = 0
    
    # Saving
    
    JSON_TYPE: str = "NocabMT"  # Version 1.0
    
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
            "index": self.index,
            "mt": self.mt_state.copy()
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
        
        self.index = jo["index"]
        self.mt_state = jo["mt"].copy()

