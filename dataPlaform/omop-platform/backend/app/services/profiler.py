import pandas as pd
import json

class DataProfiler:
    @staticmethod
    def generate_profiling(csv_path: str) -> list:
        try:
            # Read CSV (use string for all to avoid mixed type warnings on large files if dirty)
            df = pd.read_csv(csv_path, encoding='utf-8-sig', on_bad_lines='skip', dtype=str)
            
            profiling = []
            total_rows = len(df)
            
            for col in df.columns:
                series = df[col]
                
                null_count = series.isna().sum()
                null_rate = float(null_count / total_rows) if total_rows > 0 else 0
                
                # Check actual type by trying to convert to numeric
                numeric_series = pd.to_numeric(series, errors='coerce')
                
                # If more than 80% of non-null values are numeric, we classify it as numeric
                # EXCEPT for columns that are semantically identifiers or contacts
                non_null_count = series.notna().sum()
                valid_numeric_count = numeric_series.notna().sum()
                
                is_semantic_string = any(keyword in col.lower() for keyword in ['id', 'contact', 'phone', 'card', 'code', 'chief_complaint'])
                
                if not is_semantic_string and non_null_count > 0 and (valid_numeric_count / non_null_count) > 0.8:
                    type_name = 'numeric'
                    # Use numeric series for distribution to get clean numbers
                    working_series = numeric_series
                else:
                    type_name = 'string'
                    working_series = series
                
                # Top 10 value distribution
                value_counts = working_series.value_counts(dropna=True).head(10)
                distribution = [{'value': str(k), 'count': int(v)} for k, v in value_counts.items()]
                
                profiling.append({
                    'name': col,
                    'type': type_name,
                    'null_rate': round(null_rate, 4),
                    'distribution': distribution
                })
                
            return profiling
        except Exception as e:
            print(f"Profiling error: {e}")
            return []
