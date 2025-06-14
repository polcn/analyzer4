#!/usr/bin/env python3
"""
SAP Output Generator - CSV Version
Generates CSV outputs with augmented data from lookup tables.
Creates 3 CSV files that can be imported into Excel.
"""

import pandas as pd
import os
import glob
from datetime import datetime

# Constants
ENCODING_OPTIONS = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']

class LookupManager:
    """Manages all lookup data from CSV files."""
    
    def __init__(self):
        self.tables_dict = {}
        self.events_dict = {}
        self.tcodes_dict = {}
        self.fields_dict = {}
        self.activities_dict = {}
        self.object_classes_dict = {}
        self.change_indicators_dict = {}
        self.abap_sources_dict = {}
        self.load_all_lookups()
    
    def _load_csv_with_encoding(self, filename, key_col, value_col, description):
        """Load CSV file with multiple encoding attempts."""
        try:
            for encoding in ENCODING_OPTIONS:
                try:
                    df = pd.read_csv(f'data/{filename}', encoding=encoding)
                    lookup_dict = dict(zip(df[key_col], df[value_col]))
                    print(f"  - Loaded {len(lookup_dict)} {description}")
                    return lookup_dict
                except:
                    continue
            # If all encodings fail, try without specifying encoding
            df = pd.read_csv(f'data/{filename}')
            lookup_dict = dict(zip(df[key_col], df[value_col]))
            print(f"  - Loaded {len(lookup_dict)} {description}")
            return lookup_dict
        except Exception as e:
            print(f"  - Warning: Could not load {filename}: {e}")
            return {}

    def load_all_lookups(self):
        """Load all lookup files from data directory."""
        print("Loading lookup tables...")
        
        # Load all CSV lookups using helper method
        self.tables_dict = self._load_csv_with_encoding('tables.csv', 'Table', 'Table Description', 'table descriptions')
        self.events_dict = self._load_csv_with_encoding('events.csv', 'Event', 'Event Description', 'event descriptions')
        self.tcodes_dict = self._load_csv_with_encoding('tcodes.csv', 'TCode', 'TCode Description', 'tcode descriptions')
        self.fields_dict = self._load_csv_with_encoding('fields.csv', 'Field', 'Field Description', 'field descriptions')
        self.object_classes_dict = self._load_csv_with_encoding('object class.csv', 'Object Class', 'Object Class Description', 'object class descriptions')
        self.change_indicators_dict = self._load_csv_with_encoding('change indicators.csv', 'Change Indicator', 'Description', 'change indicator descriptions')
        
        # Load ACTVT.csv (special handling for Activity Code as string)
        try:
            activities_df = pd.read_csv('data/ACTVT.csv')
            self.activities_dict = dict(zip(
                activities_df['Activity Code'].astype(str), 
                activities_df['Description']
            ))
            print(f"  - Loaded {len(self.activities_dict)} activity descriptions")
        except Exception as e:
            print(f"  - Warning: Could not load ACTVT.csv: {e}")
            self.activities_dict = {}
        
        # Load ABAP source.xlsx (Excel file)
        try:
            abap_df = pd.read_excel('data/ABAP source.xlsx')
            self.abap_sources_dict = dict(zip(
                abap_df['ABAP_SOURCE'], 
                abap_df['ABAP Source Description']
            ))
            print(f"  - Loaded {len(self.abap_sources_dict)} ABAP source descriptions")
        except Exception as e:
            print(f"  - Warning: Could not load ABAP source.xlsx: {e}")
            self.abap_sources_dict = {}

def augment_table_maint_flag(flag_value, lookup_manager):
    """Augment TABLE_MAINT_FLAG with table and activity descriptions."""
    if not flag_value or pd.isna(flag_value) or flag_value == '':
        return flag_value
    
    augmented_parts = []
    flags = str(flag_value).split(' | ')
    
    for flag in flags:
        if '-' in flag and not flag.startswith('Text:'):
            parts = flag.split('-')
            if len(parts) >= 2:
                table = parts[0]
                activity = parts[1]
                
                # Get descriptions
                table_desc = lookup_manager.tables_dict.get(table, '')
                activity_desc = lookup_manager.activities_dict.get(activity, '')
                
                # Format with descriptions
                if table_desc:
                    table_part = f"{table} ({table_desc})"
                else:
                    table_part = table
                
                if activity_desc:
                    activity_part = f"{activity} ({activity_desc})"
                else:
                    activity_part = activity
                
                augmented_parts.append(f"{table_part} - {activity_part}")
            else:
                augmented_parts.append(flag)
        else:
            augmented_parts.append(flag)
    
    return ' | '.join(augmented_parts)

def _add_lookup_column(df, source_col, lookup_dict, new_col_name, position_after=None):
    """Helper function to add lookup description column after source column."""
    if source_col in df.columns:
        if position_after is None:
            position_after = source_col
        idx = df.columns.get_loc(position_after) + 1
        df.insert(idx, new_col_name, 
                 df[source_col].apply(lambda x: lookup_dict.get(str(x).strip(), '') if pd.notna(x) else ''))
    return df

def _generate_key_column(df, key_parts):
    """Generate a KEY column from specified parts."""
    def make_key(row):
        parts = []
        for part in key_parts:
            value = str(row.get(part, ''))
            parts.append(value)
        return '_'.join(parts)
    
    return df.apply(make_key, axis=1)

def process_sm20_data(df, lookup_manager):
    """Process SM20 data with augmentations."""
    print("\nProcessing SM20 data...")
    df_output = df.copy()
    
    # 1. Add KEY column as first column
    df_output.insert(0, 'KEY', _generate_key_column(df_output, ['USER', 'DATE', 'TIME']))
    
    # 2. Rename transaction code columns to TCODE if needed
    if 'TCODE' not in df_output.columns:
        if 'SOURCE_TA' in df_output.columns:
            df_output.rename(columns={'SOURCE_TA': 'TCODE'}, inplace=True)
        elif 'TRANSACTION_CODE' in df_output.columns:
            df_output.rename(columns={'TRANSACTION_CODE': 'TCODE'}, inplace=True)
    
    # 3. Add lookup columns
    df_output = _add_lookup_column(df_output, 'EVENT', lookup_manager.events_dict, 'EVENT_DESCRIPTION')
    df_output = _add_lookup_column(df_output, 'TCODE', lookup_manager.tcodes_dict, 'TCODE_DESCRIPTION')
    df_output = _add_lookup_column(df_output, 'ABAP_SOURCE', lookup_manager.abap_sources_dict, 'ABAP_SOURCE_DESCRIPTION')
    
    # 6. Augment TABLE_MAINT_FLAG with descriptions
    if 'TABLE_MAINT_FLAG' in df_output.columns:
        df_output['TABLE_MAINT_FLAG'] = df_output['TABLE_MAINT_FLAG'].apply(
            lambda x: augment_table_maint_flag(x, lookup_manager)
        )
    
    return df_output

def process_cdhdr_data(df, lookup_manager):
    """Process CDHDR data with augmentations."""
    print("\nProcessing CDHDR data...")
    df_output = df.copy()
    
    # 1. Add KEY column as first column - try multiple user column variations
    user_col = 'USERNAME' if 'USERNAME' in df_output.columns else 'USERN' if 'USERN' in df_output.columns else 'USER'
    date_col = 'UDATE' if 'UDATE' in df_output.columns else 'DATE'
    time_col = 'UTIME' if 'UTIME' in df_output.columns else 'TIME'
    df_output.insert(0, 'KEY', _generate_key_column(df_output, [user_col, date_col, time_col]))
    
    # 2. Rename transaction code columns to TCODE if needed
    if 'TCODE' not in df_output.columns:
        if 'SOURCE_TA' in df_output.columns:
            df_output.rename(columns={'SOURCE_TA': 'TCODE'}, inplace=True)
        elif 'TRANSACTION_CODE' in df_output.columns:
            df_output.rename(columns={'TRANSACTION_CODE': 'TCODE'}, inplace=True)
    
    # 3. Add TCode Description
    df_output = _add_lookup_column(df_output, 'TCODE', lookup_manager.tcodes_dict, 'TCODE_DESCRIPTION')
    
    # 4. Augment TABLE_MAINT_FLAG if present
    if 'TABLE_MAINT_FLAG' in df_output.columns:
        df_output['TABLE_MAINT_FLAG'] = df_output['TABLE_MAINT_FLAG'].apply(
            lambda x: augment_table_maint_flag(x, lookup_manager)
        )
    
    return df_output

def process_cdpos_data(df, lookup_manager):
    """Process CDPOS data with augmentations."""
    print("\nProcessing CDPOS data...")
    df_output = df.copy()
    
    # 1. Add KEY column as first column - handle table name variations
    table_col = 'TABLE NAME' if 'TABLE NAME' in df_output.columns else 'TABNAME'
    def make_cdpos_key(row):
        changenr = str(row.get('CHANGENR', ''))
        table_name = str(row.get(table_col, ''))
        tabkey = str(row.get('TABKEY', ''))[:50]  # Truncate to 50 chars
        return f"{changenr}_{table_name}_{tabkey}"
    
    df_output.insert(0, 'KEY', df_output.apply(make_cdpos_key, axis=1))
    
    # 2. Add lookup columns for various field variations
    table_col = 'TABLE NAME' if 'TABLE NAME' in df_output.columns else 'TABNAME' if 'TABNAME' in df_output.columns else None
    if table_col:
        df_output = _add_lookup_column(df_output, table_col, lookup_manager.tables_dict, 'TABLE_DESCRIPTION')
    
    obj_col = 'OBJECT' if 'OBJECT' in df_output.columns else 'OBJECTCLAS' if 'OBJECTCLAS' in df_output.columns else None
    if obj_col:
        df_output = _add_lookup_column(df_output, obj_col, lookup_manager.object_classes_dict, 'OBJECT_CLASS_DESCRIPTION')
    
    field_col = 'FIELD NAME' if 'FIELD NAME' in df_output.columns else 'FNAME' if 'FNAME' in df_output.columns else None
    if field_col:
        df_output = _add_lookup_column(df_output, field_col, lookup_manager.fields_dict, 'FIELD_DESCRIPTION')
    
    chng_col = 'CHANGE INDICATOR' if 'CHANGE INDICATOR' in df_output.columns else 'CHNGIND' if 'CHNGIND' in df_output.columns else None
    if chng_col:
        df_output = _add_lookup_column(df_output, chng_col, lookup_manager.change_indicators_dict, 'CHANGE_INDICATOR_DESCRIPTION')
    
    # 6. Augment TABLE_MAINT_FLAG if present
    if 'TABLE_MAINT_FLAG' in df_output.columns:
        df_output['TABLE_MAINT_FLAG'] = df_output['TABLE_MAINT_FLAG'].apply(
            lambda x: augment_table_maint_flag(x, lookup_manager)
        )
    
    return df_output

def create_excel_import_instructions(base_filename):
    """Create instructions for importing CSVs to Excel with formatting."""
    instructions = f"""SAP Analysis Report - Excel Import Instructions
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

FILES CREATED:
1. {base_filename}_SM20.csv
2. {base_filename}_CDHDR.csv  
3. {base_filename}_CDPOS.csv

TO CREATE FORMATTED EXCEL:

1. Open a new Excel workbook
2. Import each CSV file to a separate worksheet:
   - Data tab → From Text/CSV → Select file
   - Name worksheets: SM20, CDHDR, CDPOS

3. Format headers (Row 1 in each sheet):
   - Select entire row 1
   - Make Bold (Ctrl+B)
   - Center align
   - Remove borders

4. Highlight helper columns with #FBE2D5:
   Helper columns to highlight:
   - EVENT_DESCRIPTION
   - TCODE_DESCRIPTION
   - ABAP_SOURCE_DESCRIPTION
   - TABLE_DESCRIPTION
   - OBJECT_CLASS_DESCRIPTION
   - FIELD_DESCRIPTION
   - CHANGE_INDICATOR_DESCRIPTION
   
   For each helper column:
   - Select column header cell
   - Fill color: #FBE2D5

5. Auto-fit all columns:
   - Select all (Ctrl+A)
   - Double-click any column border

6. Save as Excel workbook (.xlsx)

NOTES:
- All data enrichments have been applied
- KEY column is the first column in each sheet
- TABLE_MAINT_FLAG includes table and activity descriptions
"""
    
    filename = f"{base_filename}_README.txt"
    with open(filename, 'w') as f:
        f.write(instructions)
    
    return filename

def generate_final_output():
    """Main function to generate CSV outputs."""
    print("SAP Output Generator")
    print("=" * 60)
    
    # Initialize lookup manager
    lookup_manager = LookupManager()
    
    # Find files
    sm20_files = glob.glob('output/*SM20*_analyzed.csv')
    cdhdr_files = glob.glob('output/*CDHDR*_cleaned.csv')
    cdpos_files = glob.glob('output/*CDPOS*_cleaned.csv')
    
    # Generate base filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_filename = f"output/SAP_Analysis_Report_{timestamp}"
    
    files_created = []
    
    # Process SM20
    if sm20_files:
        print(f"\nLoading SM20 data from: {sm20_files[0]}")
        sm20_df = pd.read_csv(sm20_files[0], encoding='utf-8-sig')
        sm20_df = process_sm20_data(sm20_df, lookup_manager)
        
        output_file = f"{base_filename}_SM20.csv"
        sm20_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        files_created.append(output_file)
        print(f"  ✅ Created: {output_file} ({len(sm20_df)} records)")
    else:
        print("\n  ⚠️  No SM20 analyzed files found")
    
    # Process CDHDR
    if cdhdr_files:
        print(f"\nLoading CDHDR data from: {cdhdr_files[0]}")
        cdhdr_df = pd.read_csv(cdhdr_files[0], encoding='utf-8-sig')
        cdhdr_df = process_cdhdr_data(cdhdr_df, lookup_manager)
        
        output_file = f"{base_filename}_CDHDR.csv"
        cdhdr_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        files_created.append(output_file)
        print(f"  ✅ Created: {output_file} ({len(cdhdr_df)} records)")
    else:
        print("\n  ⚠️  No CDHDR cleaned files found")
    
    # Process CDPOS
    if cdpos_files:
        print(f"\nLoading CDPOS data from: {cdpos_files[0]}")
        cdpos_df = pd.read_csv(cdpos_files[0], encoding='utf-8-sig')
        cdpos_df = process_cdpos_data(cdpos_df, lookup_manager)
        
        output_file = f"{base_filename}_CDPOS.csv"
        cdpos_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        files_created.append(output_file)
        print(f"  ✅ Created: {output_file} ({len(cdpos_df)} records)")
    else:
        print("\n  ⚠️  No CDPOS cleaned files found")
    
    # Create instructions file
    instructions_file = create_excel_import_instructions(base_filename)
    print(f"\n  📄 Created: {instructions_file}")
    
    # Summary
    print("\n" + "=" * 60)
    print("CSV GENERATION COMPLETE!")
    print(f"\nFiles created in output directory:")
    for file in files_created:
        print(f"  - {os.path.basename(file)}")
    print(f"  - {os.path.basename(instructions_file)}")
    
    print("\n💡 TIP: See README file for Excel import instructions")
    print("   These CSV files won't have corruption issues when imported to Excel")

def main():
    """Command line interface."""
    import sys
    
    if len(sys.argv) > 1:
        print("SAP Output Generator - CSV Version")
        print("Generates CSV files with enriched data for Excel import")
        print("\nUsage: python sap_output_generator.py")
        print("\nThis avoids Excel corruption issues by creating clean CSV files")
        print("that can be imported into Excel with manual formatting.")
    else:
        generate_final_output()

if __name__ == "__main__":
    main()