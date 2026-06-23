import pytest
from app.services.cleaning_rules import CleaningRulesEngine

def test_clean_empty_values():
    engine = CleaningRulesEngine()
    data = {"name": "Alice", "age": "", "gender": "NULL", "id": "NA", "city": "-", "status": "未知"}
    
    cleaned = engine.clean_empty_values(data)
    assert cleaned["name"] == "Alice"
    assert cleaned["age"] is None
    assert cleaned["gender"] is None
    assert cleaned["id"] is None
    assert cleaned["city"] is None
    assert cleaned["status"] is None

def test_parse_dates():
    engine = CleaningRulesEngine()
    data = {
        "dob_1": "1990-01-01",
        "dob_2": "1990/02/02",
        "dob_3": "03/04/1990",  # MM/DD/YYYY typically
        "dob_4": "1990年5月6日",
        "invalid": "not-a-date"
    }
    
    cleaned = engine.parse_dates(data, date_fields=["dob_1", "dob_2", "dob_3", "dob_4", "invalid"])
    
    assert cleaned["dob_1"] == "1990-01-01"
    assert cleaned["dob_2"] == "1990-02-02"
    assert cleaned["dob_3"] == "1990-03-04"
    assert cleaned["dob_4"] == "1990-05-06"
    assert cleaned["invalid"] is None  # Invalid dates should become None

def test_normalize_gender():
    engine = CleaningRulesEngine()
    
    assert engine.normalize_gender("男") == "M"
    assert engine.normalize_gender("M") == "M"
    assert engine.normalize_gender("1") == "M"
    
    assert engine.normalize_gender("女") == "F"
    assert engine.normalize_gender("F") == "F"
    assert engine.normalize_gender("2") == "F"
    
    assert engine.normalize_gender("未知") is None
    assert engine.normalize_gender("other") is None
