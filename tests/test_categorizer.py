import pytest
from typing import Dict, Optional

# We will import these from the module once implemented
try:
    from bot.services.categorizer import clean_business_name, auto_categorize
except ImportError:
    # Stubs to allow the file to run and fail properly initially if module doesn't exist
    def clean_business_name(raw_name: str) -> str:
        raise NotImplementedError()
        
    def auto_categorize(raw_name: str, amount: float, db_aliases: dict[str, int]) -> int | None:
        raise NotImplementedError()


def test_clean_business_name_basic() -> None:
    """Test basic cleaning: remove digits, punctuation, and extra spaces."""
    assert clean_business_name("SOME BUSINESS 123") == "SOME BUSINESS"
    assert clean_business_name("TEST-STORE*NAME.") == "TEST STORE NAME"
    assert clean_business_name("עסקה באילת חנות") == "חנות"
    assert clean_business_name("תשלום ועד בית") == "ועד בית"

def test_clean_business_name_brands() -> None:
    """Test that big brands are normalized to their standard names."""
    assert clean_business_name("מקדולנדס סניף רעננה") == "מקדונלד'ס"
    assert clean_business_name("IKEA BEER SHEVA 4940") == "IKEA"
    assert clean_business_name("CARREFOUR 123") == "CARREFOUR"
    assert clean_business_name("פנגו מוביט") == "פנגו תחבורה ציבורית"

def test_clean_business_name_suffixes() -> None:
    """Test removal of legal suffixes."""
    assert clean_business_name("משה ודוד בע\"מ") == "משה ודוד"
    assert clean_business_name("חברה בעמ") == "חברה"

def test_auto_categorize_db_alias() -> None:
    """Test that standard DB aliases are found."""
    db_aliases = {
        "WOLT": 19,
        "סופר פארם": 17
    }
    # Direct match after clean. Assuming WOLT 123 cleans to WOLT
    # Wait, clean_business_name only normalizes big brands IF they are in the list.
    # If WOLT is not in the hardcoded list, WOLT 123 -> WOLT. 
    # Let's use a known brand for the test, or rely on digit stripping.
    assert auto_categorize("WOLT 123", -50.0, db_aliases) == 19
    assert auto_categorize("UNKNOWN STORE", -50.0, db_aliases) is None

def test_auto_categorize_yellow() -> None:
    """Test dynamic rules for YELLOW / אלונית / פז (Threshold 100)."""
    db_aliases: dict[str, int] = {}
    
    # Amount is negative (expense)
    assert auto_categorize("YELLOW MARKET 123", -20.0, db_aliases) == 17  # Snacks
    assert auto_categorize("YELLOW FUEL 123", -101.0, db_aliases) == 26  # Fuel
    
    # Other gas stations
    assert auto_categorize("אלונית", -150.0, db_aliases) == 26  # Fuel
    assert auto_categorize("פז רמת גן", -40.0, db_aliases) == 17  # Snacks
    
    # Positive amount (e.g. refund) - we should check absolute value
    assert auto_categorize("YELLOW", 120.0, db_aliases) == 26  # Fuel

def test_auto_categorize_dan_deal() -> None:
    """Test dynamic rules for Dan Deal (Threshold 50)."""
    db_aliases: dict[str, int] = {}
    
    assert auto_categorize("דן דיל", -30.0, db_aliases) == 17  # Snacks
    assert auto_categorize("דן דיל", -60.0, db_aliases) == 24  # Household
