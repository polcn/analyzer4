import json
import boto3
import os

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    """
    Get analysis results and generate download URL
    
    Expected event structure (via API Gateway):
    {
        "pathParameters": {
            "analysisId": "123-456-789"
        }
    }
    """
    try:
        # Extract analysis ID
        analysis_id = event['pathParameters']['analysisId']
        
        # Get analysis metadata from DynamoDB
        table = dynamodb.Table(os.environ.get('ANALYSIS_TABLE', 'sapanalyzer4-analyses'))
        response = table.get_item(Key={'analysisId': analysis_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Analysis not found'
                })
            }
        
        item = response['Item']
        
        # Generate pre-signed URL for download if completed
        if item['status'] == 'completed':
            bucket = os.environ.get('UPLOAD_BUCKET', 'sapanalyzer4-uploads')
            download_url = s3.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': bucket,
                    'Key': item['resultKey']
                },
                ExpiresIn=3600  # 1 hour
            )
            item['downloadUrl'] = download_url
        
        # Parse summary if it's a string
        if 'summary' in item and isinstance(item['summary'], str):
            item['summary'] = json.loads(item['summary'])
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET, OPTIONS'
            },
            'body': json.dumps(item)
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