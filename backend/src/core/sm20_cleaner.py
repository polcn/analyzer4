#!/usr/bin/env python3
"""
SAP Data Cleaner - Unified cleaning for SM20, CDHDR, and CDPOS files
Consolidates three separate cleaning functions into one flexible function.
"""

import pandas as pd
import numpy as np
import os
import sys
import glob
import chardet
from datetime import datetime

# ================================================================================
# CONFIGURATION & CONSTANTS
# ================================================================================

# Columns that should be treated as string even if they look numeric
STRING_COLUMNS = ['EVENT', 'VARIABLE1', 'VARIABLE2', 'VARIABLE3', 'TERMINAL']

# File encodings to try in order
ENCODING_OPTIONS = ['utf-8', 'utf-8-sig', 'latin-1', 'iso-8859-1', 'cp1252']

# Column mapping for SM20 files
SM20_COLUMN_MAPPING = {
    # System columns
    'SYSTEMID': 'SYSTEM',
    'SYSTEM': 'SYSTEM',
    'SYS.': 'SYSTEM',
    'INST.': 'INSTANCE',
    
    # User and location columns
    'TERMINAL NAME': 'TERMINAL',
    'USER NAME': 'USER',
    'USER': 'USER',
    
    # Transaction and program columns
    'SOURCE TA': 'SOURCE_TA',
    'TRANSACTION CODE': 'TRANSACTION_CODE',
    'T-CODE': 'TRANSACTION_CODE',
    'TCODE': 'TRANSACTION_CODE',
    'ABAP SOURCE': 'ABAP_SOURCE',
    'PROGRAM': 'PROGRAM',
    
    # Event and message columns
    'AUDIT LOG MSG. TEXT': 'MESSAGE_TEXT',
    'MESSAGE TEXT': 'MESSAGE_TEXT',
    'MSG TEXT': 'MESSAGE_TEXT',
    'EVENT': 'EVENT',
    'EVENT CODE': 'EVENT',
    
    # Date and time columns
    'DATE': 'DATE',
    'TIME': 'TIME',
    
    # Variable columns - standardize all variations
    'FIRST VARIABLE VALUE FOR EVENT': 'VARIABLE1',
    'VARIABLE 2': 'VARIABLE2', 
    'VARIABLE 3': 'VARIABLE3',
    'FIRST VARIABLE': 'VARIABLE1',
    'SECOND VARIABLE': 'VARIABLE2',
    'THIRD VARIABLE': 'VARIABLE3',
    'VAR 1': 'VARIABLE1',
    'VAR 2': 'VARIABLE2',
    'VAR 3': 'VARIABLE3',
    
    # Other columns
    'CL.': 'CLASS',
    'GROUP': 'GROUP',
    'MESSAGE': 'MESSAGE_TEXT',
    'ABAP PGM': 'ABAP_SOURCE',
    'IP ADDRESS': 'PEER',
    'AUD.CLASS': 'CLASS',
    'REP': 'ABAP_SOURCE',
    
    # System ID variations
    'ID#': 'SYSAID#',
    'SYSAID': 'SYSAID#'
}

# ================================================================================
# HELPER FUNCTIONS
# ================================================================================

def _clean_string_columns(df):
    """Clean string columns by stripping whitespace and normalizing."""
    for col in df.columns:
        if df[col].dtype == 'object' or col in STRING_COLUMNS:
            # Strip whitespace
            df[col] = df[col].apply(lambda x: str(x).strip() if pd.notna(x) else '')
            # Replace various null representations with empty string
            df[col] = df[col].replace(['nan', 'None', 'NaN', 'NULL', '<NA>'], '')
            # Clean up extra whitespace
            df[col] = df[col].str.replace(r'\s+', ' ', regex=True)
            # Remove non-printable characters except newlines
            df[col] = df[col].apply(lambda x: ''.join(c for c in x if c.isprintable() or c == '\n') if x else '')
            # Replace empty-ish values
            df[col] = df[col].replace('', '')
    
    return df

def _read_file_with_encoding(input_file, file_type='csv'):
    """Read file with multiple encoding attempts for better compatibility."""
    if file_type == 'csv':
        # Try different encodings
        for encoding in ENCODING_OPTIONS:
            try:
                # First try comma-separated
                df = pd.read_csv(input_file, encoding=encoding, on_bad_lines='skip')
                
                # If only one column, try tab-delimited
                if len(df.columns) == 1:
                    print("Trying tab-delimited format...")
                    df = pd.read_csv(input_file, sep='\t', encoding=encoding, on_bad_lines='skip')
                
                # If we got here, it worked
                return df
            except UnicodeDecodeError:
                continue
        
        # If all encodings failed, try with error handling
        df = pd.read_csv(input_file, encoding='utf-8', on_bad_lines='skip', encoding_errors='replace')
    else:
        # Excel file
        df = pd.read_excel(input_file)
    
    return df

# ================================================================================
# UNIFIED CLEANING FUNCTION
# ================================================================================

def clean_sap_file(input_file, file_type='AUTO', output_file=None):
    """
    Clean any SAP export file (SM20, CDHDR, or CDPOS).
    
    Args:
        input_file: Path to SAP export file
        file_type: 'SM20', 'CDHDR', 'CDPOS', or 'AUTO' (auto-detect)
        output_file: Optional output path
    
    Returns:
        DataFrame with cleaned data
    """
    
    # Auto-detect file type if needed
    if file_type == 'AUTO':
        filename_upper = input_file.upper()
        if 'SM20' in filename_upper:
            file_type = 'SM20'
        elif 'CDHDR' in filename_upper:
            file_type = 'CDHDR'
        elif 'CDPOS' in filename_upper:
            file_type = 'CDPOS'
        else:
            # Default to SM20 if can't determine
            file_type = 'SM20'
            print(f"Warning: Could not determine file type, defaulting to SM20")
    
    print(f"Cleaning {file_type} file: {input_file}")
    
    # Determine file format
    file_format = 'xlsx' if input_file.endswith('.xlsx') else 'csv'
    
    # Read the file
    try:
        df = _read_file_with_encoding(input_file, file_format)
        print(f"Loaded {len(df)} records with {len(df.columns)} columns")
    except Exception as e:
        print(f"Error reading file: {e}")
        return None
    
    # Show original columns for SM20 (others have fewer columns)
    if file_type == 'SM20':
        print("Original columns:", list(df.columns))
    
    # 1. STANDARDIZE COLUMN NAMES
    df.columns = [col.strip().upper() for col in df.columns]
    
    # 2. APPLY FILE-SPECIFIC COLUMN MAPPINGS
    if file_type == 'SM20':
        df = df.rename(columns=SM20_COLUMN_MAPPING)
        # Show what was mapped
        for old_name, new_name in SM20_COLUMN_MAPPING.items():
            if new_name in df.columns:
                print(f"Mapped: {old_name} -> {new_name}")
    
    # 3. CREATE DATETIME COLUMN (for files with DATE and TIME)
    if 'DATE' in df.columns and 'TIME' in df.columns:
        try:
            date_str = df['DATE'].astype(str)
            time_str = df['TIME'].astype(str)
            datetime_str = date_str + ' ' + time_str
            df['DATETIME'] = pd.to_datetime(datetime_str, errors='coerce')
            print(f"Created DATETIME column from DATE + TIME")
        except Exception as e:
            print(f"Warning: Could not create datetime: {e}")
    
    # 4. CLEAN STRING COLUMNS
    df = _clean_string_columns(df)
    
    # 5. FILE-SPECIFIC POST-PROCESSING
    if file_type == 'CDHDR':
        # CDHDR specific: ensure transaction code column exists
        if 'TCODE' not in df.columns and 'TRANSACTION' in df.columns:
            df['TCODE'] = df['TRANSACTION']
        print(f"Processed {len(df)} CDHDR records")
    elif file_type == 'CDPOS':
        print(f"Processed {len(df)} CDPOS records")
    
    # 6. SAVE OUTPUT
    if output_file is None:
        # Auto-generate output filename
        filename = os.path.basename(input_file)
        base_name = os.path.splitext(filename)[0]
        output_file = f"output/{base_name}_cleaned.csv"
    
    # Create output directory if needed
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    try:
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"{file_type} saved to: {output_file}")
    except Exception as e:
        print(f"Error saving file: {e}")
        return None
    
    # Show final columns for SM20
    if file_type == 'SM20':
        print(f"Final columns: {list(df.columns)}")
    
    return df

# ================================================================================
# LEGACY WRAPPER FUNCTIONS (for backward compatibility)
# ================================================================================

def clean_sm20_file(input_file, output_file=None):
    """Legacy wrapper - maintains backward compatibility."""
    return clean_sap_file(input_file, 'SM20', output_file)

def clean_cdhdr_file(input_file, output_file=None):
    """Legacy wrapper - maintains backward compatibility."""
    return clean_sap_file(input_file, 'CDHDR', output_file)

def clean_cdpos_file(input_file, output_file=None):
    """Legacy wrapper - maintains backward compatibility."""
    return clean_sap_file(input_file, 'CDPOS', output_file)

# ================================================================================
# BATCH PROCESSING
# ================================================================================

def find_and_process_all_files():
    """Find and process all SAP files in the input directory."""
    results = {}
    
    # Create output directory if it doesn't exist
    os.makedirs('output', exist_ok=True)
    
    # Look for SM20 files
    sm20_patterns = ['input/*SM20*.csv', 'input/*sm20*.csv', 'input/*SM20*.xlsx']
    sm20_files = []
    for pattern in sm20_patterns:
        sm20_files.extend(glob.glob(pattern))
    
    if sm20_files:
        for file in sm20_files:
            if not file.endswith('_cleaned.csv'):  # Skip already cleaned files
                print(f"\nProcessing SM20 file: {file}")
                result = clean_sap_file(file, 'SM20')
                results[f'SM20_{file}'] = result is not None
    else:
        print("\nNo SM20 files found (input/*SM20*.csv or input/*SM20*.xlsx) - skipping")
    
    # Look for CDHDR files
    cdhdr_files = glob.glob('input/*CDHDR*.xlsx')
    if cdhdr_files:
        for file in cdhdr_files:
            print(f"\nProcessing CDHDR file: {file}")
            result = clean_sap_file(file, 'CDHDR')
            results[f'CDHDR_{file}'] = result is not None
    else:
        print("\nNo CDHDR files found (input/*CDHDR*.xlsx) - skipping")
    
    # Look for CDPOS files
    cdpos_files = glob.glob('input/*CDPOS*.xlsx')
    if cdpos_files:
        for file in cdpos_files:
            print(f"\nProcessing CDPOS file: {file}")
            result = clean_sap_file(file, 'CDPOS')
            results[f'CDPOS_{file}'] = result is not None
    else:
        print("\nNo CDPOS files found (input/*CDPOS*.xlsx) - skipping")
    
    # Summary
    print("\n" + "=" * 60)
    print("PROCESSING SUMMARY:")
    
    successful = 0
    total = 0
    for key, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED/SKIPPED"
        print(f"  {key}: {status}")
        if success:
            successful += 1
        total += 1
    
    print(f"\nOverall: {successful}/{total} files processed successfully")
    return results

def main():
    """Command line interface."""
    if len(sys.argv) == 1:
        # No arguments - process all files in directory
        find_and_process_all_files()
    else:
        # Legacy mode - process single file
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        
        if not os.path.exists(input_file):
            print(f"File not found: {input_file}")
            return
        
        # Use unified function with auto-detection
        result = clean_sap_file(input_file, 'AUTO', output_file)
        
        if result is not None:
            print("\nFile cleaning completed!")
        else:
            print("\nFile cleaning failed!")

if __name__ == "__main__":
    main()