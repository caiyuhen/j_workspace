import re
from typing import Dict, Any, List
from dateutil import parser as date_parser

class CleaningRulesEngine:
    """
    Engine to apply basic data cleaning and normalization rules.
    """
    
    # Common null-equivalent representations in Chinese medical data
    NULL_VALUES = {"", "null", "none", "na", "-", "未知", "不详", "无"}

    # Mock dictionary for Lookup mappings (e.g., Department Codes, ID Types)
    LOOKUP_DICTS = {
        "department": {
            "内科": "Internal Medicine",
            "外科": "Surgery",
            "儿科": "Pediatrics",
            "妇产科": "Obstetrics and Gynecology",
            "1001": "Internal Medicine",
            "1002": "Surgery"
        },
        "id_type": {
            "01": "National ID",
            "02": "Passport",
            "身份证": "National ID",
            "护照": "Passport"
        }
    }

    def clean_empty_values(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert various string representations of 'empty' into actual None.
        """
        cleaned_row = {}
        for k, v in row.items():
            if isinstance(v, str) and v.strip().lower() in self.NULL_VALUES:
                cleaned_row[k] = None
            else:
                cleaned_row[k] = v
        return cleaned_row

    def parse_dates(self, row: Dict[str, Any], date_fields: List[str]) -> Dict[str, Any]:
        """
        Attempt to parse dates into standard YYYY-MM-DD format.
        If parsing fails, returns None for that field.
        """
        cleaned_row = dict(row)
        for field in date_fields:
            val = cleaned_row.get(field)
            if not val:
                continue
            
            # Pre-process Chinese date formats
            if isinstance(val, str):
                val_str = val.replace("年", "-").replace("月", "-").replace("日", "")
                
                try:
                    # fuzzy=True helps ignore surrounding text if any
                    parsed_date = date_parser.parse(val_str, fuzzy=True)
                    cleaned_row[field] = parsed_date.strftime("%Y-%m-%d")
                except (ValueError, TypeError, OverflowError):
                    cleaned_row[field] = None
                    
        return cleaned_row

    def normalize_gender(self, val: Any) -> str | None:
        """
        Normalize gender to OMOP expected single char concepts 'M' or 'F'.
        """
        if not val:
            return None
            
        v_str = str(val).strip().lower()
        if v_str in {"男", "m", "male", "1"}:
            return "M"
        elif v_str in {"女", "f", "female", "2"}:
            return "F"
        return None

    def map_dictionary_value(self, dict_name: str, val: Any) -> Any:
        """
        Map a value using a predefined dictionary.
        If mapping fails, return the original value (or can be configured to return None/Default).
        """
        if not val or dict_name not in self.LOOKUP_DICTS:
            return val
            
        v_str = str(val).strip()
        # Case insensitive lookup
        lookup = {k.lower(): v for k, v in self.LOOKUP_DICTS[dict_name].items()}
        
        return lookup.get(v_str.lower(), val)
