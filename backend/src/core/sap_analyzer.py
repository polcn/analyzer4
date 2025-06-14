#!/usr/bin/env python3
"""
SAP Activity Analyzer - Comprehensive Analysis
Analyzes cleaned SAP audit logs to identify multiple activity types.

Input: Cleaned CSV files from sm20_cleaner.py
Output: Original data + multiple flag columns with detailed trigger information
"""

import pandas as pd
import sys
import os
import glob
import re

# === CONSTANTS ===

# Debugging detection constants
DEBUG_EVENT_CODES = [
    'A03',  # Breakpoint reached
    'A18',  # C debugging activated
    'A23',  # Goto ABAP Debugger
    'A26',  # Manually caught process stopped from debugger
    'A28',  # DB executed from debugger
    'AD3',  # Additional debug event
    'CUK',  # C debugging activated
    'CUL',  # Field content in debugger changed
    'CUM',  # Jump to ABAP Debugger
    'CUN',  # Process stopped from debugger
    'CUO',  # Explicit database operation in debugger
    'CUP',  # Non-exclusive debugging session started
]

DEBUG_TCODES = [
    'SDBG', 'SRDEBUG', 'SICF', 'JDBG', 'SA38'
]

# Table maintenance detection constants
TABLE_MAINT_TCODES = [
    'SM30',    # Call View Maintenance
    'SM31',    # Call View Maintenance Like SM30
    'SE11',    # ABAP Dictionary Maintenance
    'SM34',    # Viewcluster Maintenance
]

TABLE_MAINT_EVENT_CODES = [
    'CUE',     # Table entry changed
    'CUF',     # Table entry deleted
    'CUG',     # Table entry inserted
]

# Activity codes to flag as table maintenance (excluding 03 which is display)
TABLE_MAINT_ACTIVITIES = [
    '01', '05', '95', '06', '07', '11', '12', '16', '20', '21', 
    '23', '24', '65', '76', '25', '30', '31', '32', '34', '40', 
    '41', '42', '60', '61', '85', '90', '97', '02'
]

# High-risk table names for special monitoring
HIGH_RISK_TABLE_NAMES = ['usr02', 'ust04', 'agr_users', 'usr01', 'usr05', 'agr_1251']

# Security-related transaction codes
SECURITY_TCODES = [
    'SU01', 'SU10', 'PFCG', 'SM19', 'SU53', 'SU21', 'SU22', 'SU25', 'SU56', 'SUIM',
    'SECATT', 'RSECADMIN', 'SU24', 'SU02', 'SU05', 'SU12', 'PFUD', 'SPRO'
]

# Configuration-related transaction codes
CONFIG_TCODES = [
    'SPRO', 'SM30', 'OX02', 'OVZG', 'OVZH', 'RZ10', 'RZ11', 'SM59', 'WE20', 'WE21',
    'SALE', 'BD54', 'BD64', 'SM25', 'SCOT', 'SOST', 'SO10', 'SCC4', 'SCC1'
]

# Transport-related transaction codes
TRANSPORT_TCODES = [
    'STMS', 'SE01', 'SE09', 'SE10', 'SE03', 'CTS', 'STMS_IMPORT', 'SCC1',
    'STMS_QA', 'CG3Y', 'CG3Z'
]

# Job scheduling transaction codes
JOB_SCHEDULE_TCODES = [
    'SM36', 'SM37', 'SM62', 'SM64', 'SM65', 'SM66', 'RZ20', 'SWEL', 'SXMB_MONI',
    'AL11', 'SM21', 'ST05', 'ST06', 'ST22'
]

# Security patterns for text analysis
SECURITY_PATTERNS = [
    ('USER ADMINISTRATION', 'USER_ADMINISTRATION'),
    ('AUTHORIZATION FAILED', 'AUTHORIZATION_FAILED'),  
    ('AUTHORIZATION CHECK', 'AUTHORIZATION_CHECK'),
    ('USER PROFILE', 'USER_PROFILE'),
    ('SECURITY PROFILE', 'SECURITY_PROFILE'),
    ('PASSWORD', 'PASSWORD'),
    ('ROLE ASSIGNMENT', 'ROLE_ASSIGNMENT'),
    ('PERMISSION', 'PERMISSION')
]

# Configuration keywords
CONFIG_KEYWORDS = ['CUSTOMIZING', 'CONFIGURATION', 'SYSTEM PARAMETER', 'VARIANT']

# Transport keywords
TRANSPORT_KEYWORDS = ['TRANSPORT REQUEST', 'CHANGE REQUEST', 'WORKBENCH REQUEST', 'IMPORT', 'EXPORT']

# Job scheduling keywords
JOB_KEYWORDS = ['BACKGROUND JOB', 'JOB SCHEDULE', 'BATCH JOB', 'PERIODIC JOB']

# Change indicator mappings for CDPOS
CHANGE_INDICATORS = {
    'U': 'Update',
    'I': 'Insert',
    'D': 'Delete',
    'E': 'Delete',  # Sometimes E is used for delete
    'J': 'Key Insert',
    'K': 'Key Delete'
}

# === GLOBAL VARIABLES ===
HIGH_RISK_TABLES = set()
HIGH_RISK_TCODES = {}

def _load_lookup_data():
    """Load lookup data from CSV files."""
    global HIGH_RISK_TABLES, HIGH_RISK_TCODES
    
    # Load high-risk tables
    try:
        hr_tables_df = pd.read_csv('data/high_risk_tables.csv')
        HIGH_RISK_TABLES = set(hr_tables_df['Table'].str.upper())
        print(f"Loaded {len(HIGH_RISK_TABLES)} high-risk tables for monitoring")
    except Exception as e:
        print(f"Warning: Could not load high_risk_tables.csv: {e}")
        HIGH_RISK_TABLES = set()
    
    # Load high-risk transaction codes
    try:
        df = pd.read_csv('data/high_risk_tcodes.csv')
        HIGH_RISK_TCODES = dict(zip(df['TCode'].str.upper(), df['Category']))
        print(f"Loaded {len(HIGH_RISK_TCODES)} high-risk transaction codes")
    except Exception as e:
        print(f"Warning: Could not load high_risk_tcodes.csv: {e}")
        HIGH_RISK_TCODES = {}

# Load lookup data when module is imported
_load_lookup_data()

# === HELPER FUNCTIONS ===

def _check_text_for_pattern(text, pattern):
    """Check if text contains pattern (case-insensitive)."""
    if not text or pd.isna(text):
        return False
    return pattern.lower() in str(text).lower()

def _extract_table_from_message(msg_text, activity_code):
    """Extract table name from generic table access message."""
    if not msg_text:
        return None
    pattern = rf'generic table access call to (\w+) with activity {activity_code}'
    match = re.search(pattern, msg_text.lower())
    return match.group(1).upper() if match else None

def _check_high_risk_table_activity(msg_text):
    """Check for high-risk table maintenance activities."""
    if not msg_text:
        return None
    
    msg_lower = msg_text.lower()
    for table in HIGH_RISK_TABLE_NAMES:
        if table in msg_lower:
            # Check if any maintenance activity is present
            for activity_code in TABLE_MAINT_ACTIVITIES:
                if f'activity {activity_code}' in msg_lower:
                    return table.upper()
    return None

def _deduplicate_triggers(triggers):
    """Remove duplicate triggers while preserving order."""
    seen = set()
    unique_triggers = []
    for trigger in triggers:
        # Extract tcode from trigger for deduplication
        tcode_part = trigger.split(':')[1] if ':' in trigger else trigger
        if tcode_part not in seen:
            seen.add(tcode_part)
            unique_triggers.append(trigger)
    return unique_triggers

def detect_debugging(row):
    """
    Detect debugging activity in a single row.
    Returns formatted string with triggers or empty string if no debugging detected.
    """
    triggers = []
    
    # 1. Check EVENT column
    event = str(row.get('EVENT', '')).upper().strip()
    if event in DEBUG_EVENT_CODES:
        triggers.append(f"Event:{event}")
    
    # 2. Check TRANSACTION_CODE column
    tcode = str(row.get('TRANSACTION_CODE', '')).upper().strip()
    if tcode in DEBUG_TCODES:
        triggers.append(f"TCode:{tcode}")
    
    # 3. Check text fields for *debug* pattern (case-insensitive)
    text_columns = ['MESSAGE_TEXT', 'ABAP_SOURCE', 'SOURCE_TA']
    for col in text_columns:
        if col in row:
            text = str(row[col]).lower()
            if 'debug' in text and text.strip():  # Only if not empty
                triggers.append(f"{col}:*debug*")
    
    # 4. Check VARIABLE2 for value 200
    var2 = str(row.get('VARIABLE2', '')).strip()
    if var2 == '200':
        triggers.append("Var2:200")
    
    # 5. Check VARIABLE3 for "CODE -> EDIT"
    var3 = str(row.get('VARIABLE3', '')).strip()
    if 'CODE -> EDIT' in var3:
        triggers.append("Var3:CODE->EDIT")
    
    # Format output using pipe separator for clarity
    if triggers:
        return ' | '.join(triggers)
    else:
        return ''

def detect_table_maintenance(row):
    """
    Detect table maintenance activity in a single row.
    Returns formatted string with triggers or empty string if no table maintenance detected.
    """
    triggers = []
    
    # 1. Check EVENT column for table maintenance events
    event = str(row.get('EVENT', '')).upper().strip()
    if event in TABLE_MAINT_EVENT_CODES:
        triggers.append(f"Event:{event}")
    
    # 2. Check TRANSACTION_CODE column
    tcode = str(row.get('TRANSACTION_CODE', '')).upper().strip()
    if tcode in TABLE_MAINT_TCODES:
        triggers.append(f"TCode:{tcode}")
    
    # 3. Check message text for table maintenance activity patterns
    msg_text = str(row.get('MESSAGE_TEXT', ''))
    msg_lower = msg_text.lower()
    
    # Look for "Generic table access call to [TABLE] with activity [CODE]" pattern
    for activity_code in TABLE_MAINT_ACTIVITIES:
        activity_pattern = f'activity {activity_code}'
        if activity_pattern in msg_lower:
            if 'generic table access call to' in msg_lower:
                # Try to extract table name
                table_name = _extract_table_from_message(msg_text, activity_code)
                if table_name:
                    triggers.append(f"{table_name}-{activity_code}")
                else:
                    triggers.append(f"Text:activity_{activity_code}")
            else:
                triggers.append(f"Text:activity_{activity_code}")
            break  # Only match the first activity code found
    
    # 4. Check for table maintenance keywords (but not generic access)
    if _check_text_for_pattern(msg_text, 'table maintenance'):
        triggers.append("Text:table_maintenance")
    
    # 5. Check for specific high-risk table names with any maintenance activity
    high_risk_table = _check_high_risk_table_activity(msg_text)
    if high_risk_table:
        triggers.append(f"HighRiskTable:{high_risk_table}")
    
    # Format output using pipe separator
    if triggers:
        return ' | '.join(triggers)
    else:
        return ''

def detect_high_risk_tcode(row):
    """
    Detect high-risk transaction code usage in a single row.
    Searches TRANSACTION_CODE, MESSAGE_TEXT, and VARIABLE1 fields.
    Returns formatted string with triggers or empty string if no high-risk tcodes detected.
    """
    triggers = []
    import re
    
    # 1. Check TRANSACTION_CODE column (exact match)
    tcode = str(row.get('TRANSACTION_CODE', '')).upper().strip()
    if tcode in HIGH_RISK_TCODES:
        category = HIGH_RISK_TCODES[tcode].replace(' ', '_')
        triggers.append(f"TCode:{tcode}:{category}")
    
    # 2. Check MESSAGE_TEXT for transaction code mentions
    msg_text = str(row.get('MESSAGE_TEXT', '')).upper()
    if msg_text.strip():
        for tcode_key, category in HIGH_RISK_TCODES.items():
            # Use word boundary matching to avoid false positives
            pattern = rf'\b{re.escape(tcode_key)}\b'
            if re.search(pattern, msg_text):
                category_clean = category.replace(' ', '_')
                triggers.append(f"Text:{tcode_key}:{category_clean}")
                break  # Only match the first high-risk tcode found in text
    
    # 3. Check VARIABLE1 for transaction code values
    var1 = str(row.get('VARIABLE1', '')).upper().strip()
    if var1 in HIGH_RISK_TCODES:
        category = HIGH_RISK_TCODES[var1].replace(' ', '_')
        triggers.append(f"Var1:{var1}:{category}")
    
    # Remove duplicates while preserving order
    unique_triggers = _deduplicate_triggers(triggers)
    
    # Format output using pipe separator
    if unique_triggers:
        return ' | '.join(unique_triggers)
    else:
        return ''

def detect_high_risk_table(row):
    """
    Detect high-risk table access in CDPOS records.
    Checks the TABLE NAME field against the high_risk_tables.csv list.
    Returns formatted string with table name or empty string if not high-risk.
    """
    # Get table name from row
    table_name = str(row.get('TABLE NAME', '')).upper().strip()
    
    # Check if this is a high-risk table
    if table_name in HIGH_RISK_TABLES:
        # Also check the change indicator for context
        change_indicator = str(row.get('CHANGE INDICATOR', '')).upper().strip()
        indicator_desc = CHANGE_INDICATORS.get(change_indicator, change_indicator)
        
        if indicator_desc:
            return f"{table_name}:{indicator_desc}"
        else:
            return table_name
    
    return ''

def detect_other_flags(row):
    """
    Detect other SAP activity flags in a single row.
    Searches for SECURITY, CONFIG, TRANSPORT, and JOB_SCHEDULE activities.
    Returns formatted string with triggers or empty string if no activities detected.
    """
    triggers = []
    
    # Get transaction code and message text for analysis
    tcode = str(row.get('TRANSACTION_CODE', '')).upper().strip()
    msg_text = str(row.get('MESSAGE_TEXT', '')).upper()
    
    # 1. SECURITY_FLAG - Check for security-related activities
    if tcode in SECURITY_TCODES:
        triggers.append(f"Security:TCode:{tcode}")
    elif any(sec_tcode in msg_text for sec_tcode in SECURITY_TCODES):
        # Find which security tcode was mentioned in message
        for sec_tcode in SECURITY_TCODES:
            if sec_tcode in msg_text:
                triggers.append(f"Security:Text:{sec_tcode}")
                break
    # Check for security-related keywords in message text
    for pattern, flag_name in SECURITY_PATTERNS:
        if pattern in msg_text:
            triggers.append(f"Security:Text:{flag_name}")
            break
    
    # 2. CONFIG_FLAG - Check for configuration activities
    if tcode in CONFIG_TCODES:
        triggers.append(f"Config:TCode:{tcode}")
    elif any(config_tcode in msg_text for config_tcode in CONFIG_TCODES):
        # Find which config tcode was mentioned in message
        for config_tcode in CONFIG_TCODES:
            if config_tcode in msg_text:
                triggers.append(f"Config:Text:{config_tcode}")
                break
    # Check for configuration keywords
    for keyword in CONFIG_KEYWORDS:
        if keyword in msg_text:
            triggers.append(f"Config:Text:{keyword.replace(' ', '_')}")
            break
    
    # 3. TRANSPORT_FLAG - Check for transport activities
    if tcode in TRANSPORT_TCODES:
        triggers.append(f"Transport:TCode:{tcode}")
    elif any(trans_tcode in msg_text for trans_tcode in TRANSPORT_TCODES):
        # Find which transport tcode was mentioned in message
        for trans_tcode in TRANSPORT_TCODES:
            if trans_tcode in msg_text:
                triggers.append(f"Transport:Text:{trans_tcode}")
                break
    # Check for transport keywords
    for keyword in TRANSPORT_KEYWORDS:
        if keyword in msg_text:
            triggers.append(f"Transport:Text:{keyword.replace(' ', '_')}")
            break
    
    # 4. JOB_SCHEDULE_FLAG - Check for job scheduling activities
    if tcode in JOB_SCHEDULE_TCODES:
        triggers.append(f"JobSchedule:TCode:{tcode}")
    elif any(job_tcode in msg_text for job_tcode in JOB_SCHEDULE_TCODES):
        # Find which job tcode was mentioned in message
        for job_tcode in JOB_SCHEDULE_TCODES:
            if job_tcode in msg_text:
                triggers.append(f"JobSchedule:Text:{job_tcode}")
                break
    # Check for job scheduling keywords
    for keyword in JOB_KEYWORDS:
        if keyword in msg_text:
            triggers.append(f"JobSchedule:Text:{keyword.replace(' ', '_')}")
            break
    
    # Format output using pipe separator
    if triggers:
        return ' | '.join(triggers)
    else:
        return ''

def analyze_sap_activities(input_file, output_file=None):
    """
    Analyze a cleaned SAP file for multiple activity types.
    Detects file type (SM20, CDHDR, CDPOS) and applies appropriate flags.
    """
    print(f"\nAnalyzing SAP activities in: {input_file}")
    
    # Detect file type from filename
    file_type = 'UNKNOWN'
    filename_upper = os.path.basename(input_file).upper()
    if 'SM20' in filename_upper:
        file_type = 'SM20'
    elif 'CDHDR' in filename_upper:
        file_type = 'CDHDR'
    elif 'CDPOS' in filename_upper:
        file_type = 'CDPOS'
    
    print(f"Detected file type: {file_type}")
    
    # Read the cleaned CSV
    try:
        df = pd.read_csv(input_file, encoding='utf-8-sig')
        print(f"Loaded {len(df)} records")
    except Exception as e:
        print(f"Error reading file: {e}")
        return None
    
    # Apply detection functions based on file type
    print("\nApplying activity detection...")
    
    if file_type == 'SM20':
        # SM20 gets all flags
        # Add DEBUG_FLAG column
        df['DEBUG_FLAG'] = df.apply(detect_debugging, axis=1)
        debug_count = (df['DEBUG_FLAG'] != '').sum()
        print(f"  - Found {debug_count} debugging activities")
        
        # Add TABLE_MAINT_FLAG column
        df['TABLE_MAINT_FLAG'] = df.apply(detect_table_maintenance, axis=1)
        table_maint_count = (df['TABLE_MAINT_FLAG'] != '').sum()
        print(f"  - Found {table_maint_count} table maintenance activities")
        
        # Add HIGH_RISK_TCODE_FLAG column
        df['HIGH_RISK_TCODE_FLAG'] = df.apply(detect_high_risk_tcode, axis=1)
        high_risk_count = (df['HIGH_RISK_TCODE_FLAG'] != '').sum()
        print(f"  - Found {high_risk_count} high-risk transaction code activities")
        
        # Add OTHER_FLAGS column (Security, Config, Transport, Job Schedule)
        df['OTHER_FLAGS'] = df.apply(detect_other_flags, axis=1)
        other_flags_count = (df['OTHER_FLAGS'] != '').sum()
        print(f"  - Found {other_flags_count} other flag activities (Security/Config/Transport/JobSchedule)")
        
    elif file_type == 'CDHDR':
        # CDHDR gets HIGH_RISK_TCODE_FLAG
        df['HIGH_RISK_TCODE_FLAG'] = df.apply(detect_high_risk_tcode, axis=1)
        high_risk_count = (df['HIGH_RISK_TCODE_FLAG'] != '').sum()
        print(f"  - Found {high_risk_count} high-risk transaction code activities")
        
    elif file_type == 'CDPOS':
        # CDPOS gets HIGH_RISK_TABLE_FLAG
        df['HIGH_RISK_TABLE_FLAG'] = df.apply(detect_high_risk_table, axis=1)
        high_risk_table_count = (df['HIGH_RISK_TABLE_FLAG'] != '').sum()
        print(f"  - Found {high_risk_table_count} high-risk table modifications")
    
    else:
        print("  - Warning: Unknown file type, no flags applied")
    
    # Show sample of activities found based on file type
    if file_type == 'SM20':
        if 'debug_count' in locals() and debug_count > 0:
            print("\nSample debugging activities:")
            debug_samples = df[df['DEBUG_FLAG'] != '']['DEBUG_FLAG'].value_counts().head(5)
            for pattern, count in debug_samples.items():
                print(f"  {pattern}: {count} occurrences")
        
        if 'table_maint_count' in locals() and table_maint_count > 0:
            print("\nSample table maintenance activities:")
            table_samples = df[df['TABLE_MAINT_FLAG'] != '']['TABLE_MAINT_FLAG'].value_counts().head(5)
            for pattern, count in table_samples.items():
                print(f"  {pattern}: {count} occurrences")
        
        if 'high_risk_count' in locals() and high_risk_count > 0:
            print("\nSample high-risk transaction code activities:")
            high_risk_samples = df[df['HIGH_RISK_TCODE_FLAG'] != '']['HIGH_RISK_TCODE_FLAG'].value_counts().head(5)
            for pattern, count in high_risk_samples.items():
                print(f"  {pattern}: {count} occurrences")
        
        if 'other_flags_count' in locals() and other_flags_count > 0:
            print("\nSample other flag activities:")
            other_samples = df[df['OTHER_FLAGS'] != '']['OTHER_FLAGS'].value_counts().head(5)
            for pattern, count in other_samples.items():
                print(f"  {pattern}: {count} occurrences")
                
    elif file_type == 'CDHDR':
        if 'high_risk_count' in locals() and high_risk_count > 0:
            print("\nSample high-risk transaction code activities:")
            high_risk_samples = df[df['HIGH_RISK_TCODE_FLAG'] != '']['HIGH_RISK_TCODE_FLAG'].value_counts().head(5)
            for pattern, count in high_risk_samples.items():
                print(f"  {pattern}: {count} occurrences")
                
    elif file_type == 'CDPOS':
        if 'high_risk_table_count' in locals() and high_risk_table_count > 0:
            print("\nSample high-risk table modifications:")
            table_samples = df[df['HIGH_RISK_TABLE_FLAG'] != '']['HIGH_RISK_TABLE_FLAG'].value_counts().head(5)
            for pattern, count in table_samples.items():
                print(f"  {pattern}: {count} occurrences")
    
    # Save output
    if output_file is None:
        # Extract filename and save to output directory
        filename = os.path.basename(input_file)
        base_name = os.path.splitext(filename)[0]
        # Remove any existing _analyzed suffix to avoid duplication
        if base_name.endswith('_analyzed'):
            base_name = base_name[:-9]
        output_file = f"output/{base_name}_analyzed.csv"
    
    try:
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\nSaved analyzed data to: {output_file}")
    except Exception as e:
        print(f"Error saving file: {e}")
        return None
    
    return df

def analyze_all_cleaned_files():
    """
    Find and analyze all cleaned SAP files (SM20, CDHDR, CDPOS) in the output directory.
    """
    print("SAP Activity Analyzer - Comprehensive Analysis")
    print("=" * 60)
    
    # Ensure output directory exists
    os.makedirs('output', exist_ok=True)
    
    # Look for all cleaned files in output directory
    sm20_files = glob.glob('output/*SM20*_cleaned.csv')
    cdhdr_files = glob.glob('output/*CDHDR*_cleaned.csv')
    cdpos_files = glob.glob('output/*CDPOS*_cleaned.csv')
    
    all_cleaned_files = sm20_files + cdhdr_files + cdpos_files
    
    if not all_cleaned_files:
        print("No cleaned files found in output directory")
        print("Looking for: *SM20*_cleaned.csv, *CDHDR*_cleaned.csv, *CDPOS*_cleaned.csv")
        print("Please run sm20_cleaner.py first to clean your data files.")
        return
    
    print(f"Found {len(all_cleaned_files)} cleaned files to analyze:")
    print(f"  - {len(sm20_files)} SM20 files")
    print(f"  - {len(cdhdr_files)} CDHDR files")  
    print(f"  - {len(cdpos_files)} CDPOS files")
    
    # Process each file
    for file in all_cleaned_files:
        # Skip already analyzed files
        if '_analyzed.csv' in file:
            continue
            
        result = analyze_sap_activities(file)
        if result is not None:
            print(f"✅ Successfully analyzed {file}")
        else:
            print(f"❌ Failed to analyze {file}")
    
    print("\n" + "=" * 60)
    print("Analysis complete!")

def main():
    """Command line interface."""
    if len(sys.argv) == 1:
        # No arguments - analyze all cleaned files
        analyze_all_cleaned_files()
    else:
        # Analyze specific file
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        
        if not os.path.exists(input_file):
            print(f"File not found: {input_file}")
            return
        
        result = analyze_sap_activities(input_file, output_file)
        if result is not None:
            print("\nActivity analysis completed!")
        else:
            print("\nActivity analysis failed!")

if __name__ == "__main__":
    main()