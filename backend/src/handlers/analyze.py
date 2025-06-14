import json
import boto3
import os
import tempfile
import traceback
from datetime import datetime
import sys
sys.path.append('/opt/python')

# Import core analysis modules
from core.sm20_cleaner import sm20Cleaner
from core.sap_analyzer import SAPAnalyzer
from core.sap_output_generator import SAPOutputGenerator

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    """
    Lambda handler for SAP file analysis
    
    Expected event structure:
    {
        "bucket": "sapanalyzer4-uploads",
        "key": "uploads/123/SM20_export.csv",
        "analysisId": "123",
        "fileType": "SM20"  # or "CDHDR" or "CDPOS"
    }
    """
    try:
        # Extract parameters
        bucket = event['bucket']
        key = event['key']
        analysis_id = event['analysisId']
        file_type = event.get('fileType', 'SM20')
        
        # Create temp directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Download file from S3
            input_file = os.path.join(temp_dir, 'input.csv')
            s3.download_file(bucket, key, input_file)
            
            # Step 1: Clean the file
            cleaner = sm20Cleaner()
            cleaned_file = os.path.join(temp_dir, 'cleaned.csv')
            
            if file_type == 'SM20':
                cleaner.clean_sm20(input_file, cleaned_file)
            elif file_type == 'CDHDR':
                cleaner.clean_cdhdr(input_file, cleaned_file)
            elif file_type == 'CDPOS':
                cleaner.clean_cdpos(input_file, cleaned_file)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
            
            # Step 2: Analyze the cleaned file
            analyzer = SAPAnalyzer()
            analyzed_file = os.path.join(temp_dir, 'analyzed.csv')
            
            # Run analysis
            summary = analyzer.analyze_files(
                sm20_file=cleaned_file if file_type == 'SM20' else None,
                cdhdr_file=cleaned_file if file_type == 'CDHDR' else None,
                cdpos_file=cleaned_file if file_type == 'CDPOS' else None,
                output_dir=temp_dir
            )
            
            # Step 3: Generate enriched output
            generator = SAPOutputGenerator()
            enriched_files = generator.generate_outputs(temp_dir, temp_dir)
            
            # Upload results to S3
            results_key = f"results/{analysis_id}/{file_type}_analyzed.csv"
            
            # Find the enriched file
            for file in enriched_files:
                if file_type.lower() in file.lower():
                    s3.upload_file(file, bucket, results_key)
                    break
            
            # Store analysis metadata in DynamoDB
            table = dynamodb.Table(os.environ.get('ANALYSIS_TABLE', 'sapanalyzer4-analyses'))
            table.put_item(
                Item={
                    'analysisId': analysis_id,
                    'timestamp': datetime.utcnow().isoformat(),
                    'fileType': file_type,
                    'inputKey': key,
                    'resultKey': results_key,
                    'summary': json.dumps(summary),
                    'status': 'completed'
                }
            )
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'analysisId': analysis_id,
                    'resultKey': results_key,
                    'summary': summary
                })
            }
            
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        print(traceback.format_exc())
        
        # Update status in DynamoDB
        if 'analysis_id' in locals():
            table = dynamodb.Table(os.environ.get('ANALYSIS_TABLE', 'sapanalyzer4-analyses'))
            table.put_item(
                Item={
                    'analysisId': analysis_id,
                    'timestamp': datetime.utcnow().isoformat(),
                    'status': 'failed',
                    'error': str(e)
                }
            )
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }