# SAPAnalyzer4

AWS serverless SAP audit log analyzer with web interface. Built on the proven analysis engine from SAPAnalyzer3.

## Architecture

- **Frontend**: React SPA hosted on S3/CloudFront
- **Backend**: AWS Lambda functions via API Gateway
- **Storage**: S3 for file uploads, DynamoDB for results
- **Infrastructure**: AWS CDK for one-command deployment

## Features

- Upload and analyze SAP export files (SM20, CDHDR, CDPOS)
- Real-time analysis with security detection flags
- Download results as CSV
- Pay-per-use pricing model (near-zero idle costs)

## Quick Start

### Prerequisites
- AWS CLI configured
- Node.js 18+ and Python 3.12+
- AWS CDK CLI: `npm install -g aws-cdk`

### Local Development

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m pytest

# Frontend
cd frontend
npm install
npm start
```

### Deploy to AWS

```bash
cd infrastructure
npm install
cdk deploy
```

## Project Structure

```
sapanalyzer4/
├── backend/          # Lambda functions
├── frontend/         # React application
├── infrastructure/   # AWS CDK code
└── docs/            # Documentation
```

## Cost Optimization

- Lambda functions scale to zero when not in use
- S3 lifecycle policies for temporary files
- DynamoDB on-demand pricing
- CloudFront caching for static assets

Typical costs:
- Idle: ~$1-2/month
- Per analysis: ~$0.01-0.05