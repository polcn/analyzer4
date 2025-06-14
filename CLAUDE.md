# CLAUDE.md - AI Assistant Context

This document provides context for AI assistants working on the SAPAnalyzer4 project.

## Project Overview

SAPAnalyzer4 is an AWS serverless web application for analyzing SAP audit logs. It's built on the proven analysis engine from SAPAnalyzer3 but with a modern cloud architecture.

### Key Features
- Analyzes SAP export files (SM20, CDHDR, CDPOS)
- Detects security risks and compliance issues
- Serverless architecture with pay-per-use pricing
- Web interface for easy file upload and results viewing

## Architecture

### Backend (AWS Lambda)
- **Language**: Python 3.12
- **Core Logic**: Reused from SAPAnalyzer3 (sm20_cleaner.py, sap_analyzer.py, sap_output_generator.py)
- **Handlers**:
  - `upload.py`: Generates pre-signed URLs for S3 uploads
  - `analyze.py`: Processes uploaded files and runs analysis
  - `get_results.py`: Retrieves analysis results

### Frontend (React)
- **Framework**: React 18 with react-scripts
- **Key Components**:
  - `FileUpload.js`: Drag-and-drop file upload interface
  - `AnalysisResults.js`: Displays analysis results and download links
- **Styling**: Custom CSS with responsive design

### Infrastructure (AWS CDK)
- **S3 Buckets**: File storage with lifecycle policies
- **API Gateway**: RESTful API endpoints
- **DynamoDB**: Stores analysis metadata
- **CloudFront**: CDN for frontend hosting
- **Lambda Functions**: Serverless compute

## Development Workflow

### Local Setup
```bash
./setup-local.sh  # Sets up all dependencies
```

### Testing
- Backend: `cd backend && python -m pytest`
- Frontend: `cd frontend && npm test`

### Deployment
```bash
cd frontend && npm run build
cd ../infrastructure
cdk deploy
```

## Cost Optimization
- Lambda functions scale to zero when idle
- S3 lifecycle rules delete old files after 30 days
- DynamoDB uses on-demand pricing
- Estimated costs: $1-2/month idle, $0.01-0.05 per analysis

## GitHub Repository
- **URL**: https://github.com/polcn/analyzer4
- **Branch**: main
- **Status**: Initial version deployed

## Important Notes

### Security
- All file uploads use pre-signed S3 URLs
- Lambda functions have minimal IAM permissions
- CORS is configured for API Gateway

### File Processing
- Maximum file size: Limited by Lambda timeout (15 minutes)
- Supported formats: CSV, XLS, XLSX
- Analysis includes 7 detection flags from SAPAnalyzer3

### Future Enhancements
- User authentication and multi-tenancy
- Batch file processing
- Enhanced reporting dashboard
- API rate limiting
- Custom domain setup with existing GoDaddy domain

## Common Tasks

### Add New Detection Flag
1. Update `sap_analyzer.py` with new flag logic
2. Update frontend to display new flag
3. Test with sample data
4. Deploy updates

### Update Dependencies
1. Backend: Update `requirements.txt`
2. Frontend: Update `package.json`
3. Infrastructure: Update CDK version
4. Test thoroughly before deploying

### Debug Lambda Functions
- Check CloudWatch logs in AWS Console
- Use `console.log()` in Lambda handlers
- Test locally with sample events

## Contact
- Repository: https://github.com/polcn/analyzer4
- Based on: SAPAnalyzer3 (../analyzer3)