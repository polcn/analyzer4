import json
import boto3
import uuid
import os
from datetime import datetime

s3 = boto3.client('s3')

def lambda_handler(event, context):
    """
    Generate pre-signed URL for file upload
    
    Expected event structure:
    {
        "fileName": "SM20_export.csv",
        "fileType": "SM20"
    }
    """
    try:
        # Parse request
        body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        file_name = body['fileName']
        file_type = body.get('fileType', 'SM20')
        
        # Generate unique analysis ID
        analysis_id = str(uuid.uuid4())
        
        # Create S3 key
        key = f"uploads/{analysis_id}/{file_name}"
        bucket = os.environ.get('UPLOAD_BUCKET', 'sapanalyzer4-uploads')
        
        # Generate pre-signed URL for upload
        presigned_url = s3.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': bucket,
                'Key': key,
                'ContentType': 'text/csv'
            },
            ExpiresIn=3600  # 1 hour
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            },
            'body': json.dumps({
                'uploadUrl': presigned_url,
                'analysisId': analysis_id,
                'key': key
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': str(e)
            })
        }