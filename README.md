# SAPAnalyzer4

AWS serverless SAP audit log analyzer with web interface. Built on the proven analysis engine from SAPAnalyzer3.

## 🚀 Live Demo

Repository: [https://github.com/polcn/analyzer4](https://github.com/polcn/analyzer4)

## Overview

SAPAnalyzer4 processes SAP security audit logs (SM20), change documents (CDHDR/CDPOS), and applies advanced detection algorithms to identify:
- Debugging activities
- High-risk transaction usage
- Sensitive table modifications
- Security configuration changes
- Unauthorized access attempts

## Architecture

- **Frontend**: React SPA hosted on S3/CloudFront
- **Backend**: AWS Lambda functions via API Gateway
- **Storage**: S3 for file uploads, DynamoDB for results
- **Infrastructure**: AWS CDK for one-command deployment

## Features

- ✅ Upload and analyze SAP export files (SM20, CDHDR, CDPOS)
- ✅ Real-time analysis with 7 security detection flags
- ✅ Download enriched results as CSV
- ✅ Pay-per-use pricing model (near-zero idle costs)
- ✅ 830K+ SAP table descriptions and 30K+ transaction codes
- ✅ Professional web interface with drag-and-drop upload

## Quick Start

### Prerequisites
- AWS Account with appropriate permissions
- AWS CLI configured
- Node.js 18+ and Python 3.12+
- AWS CDK CLI: `npm install -g aws-cdk`

### Option 1: Quick Setup Script

```bash
git clone https://github.com/polcn/analyzer4.git
cd analyzer4
./setup-local.sh
```

### Option 2: Manual Setup

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install

# Infrastructure
cd ../infrastructure
npm install
```

### Deploy to AWS

```bash
# Build frontend
cd frontend
npm run build

# Deploy everything
cd ../infrastructure
cdk bootstrap  # First time only
cdk deploy
```

The deployment will output:
- API Gateway URL
- CloudFront website URL
- S3 bucket name

## Project Structure

```
sapanalyzer4/
├── backend/              # Lambda functions
│   ├── src/
│   │   ├── handlers/    # Lambda handlers
│   │   ├── core/        # Analysis engine (from SAPAnalyzer3)
│   │   └── data/        # Lookup tables
│   └── requirements.txt
├── frontend/            # React application
│   ├── src/
│   │   ├── components/  # UI components
│   │   └── services/    # API integration
│   └── package.json
├── infrastructure/      # AWS CDK code
│   └── lib/
│       └── sapanalyzer4-stack.ts
├── docs/               # Documentation
│   └── DEPLOYMENT.md
├── CLAUDE.md          # AI assistant context
└── setup-local.sh     # Setup script
```

## Cost Optimization

- **Lambda**: Scale to zero when not in use
- **S3**: Automatic cleanup after 30 days
- **DynamoDB**: Pay-per-request pricing
- **CloudFront**: Efficient caching

### Estimated Costs
- **Idle**: ~$1-2/month (S3 + CloudFront)
- **Per analysis**: ~$0.01-0.05
- **Monthly (100 analyses)**: ~$5
- **Monthly (1000 analyses)**: ~$20-30

## Development

### Run Tests
```bash
# Backend
cd backend
python -m pytest

# Frontend
cd frontend
npm test
```

### Update and Deploy
```bash
# Make changes, then:
cd infrastructure
cdk diff  # Preview changes
cdk deploy
```

## Detection Capabilities

### Supported File Types
- **SM20**: Security Audit Log
- **CDHDR**: Change Documents Header
- **CDPOS**: Change Documents Items

### Detection Flags
1. **DEBUG_FLAG**: Debugging and code modification activities
2. **TABLE_MAINT_FLAG**: Direct table maintenance operations
3. **HIGH_RISK_TCODE_FLAG**: Usage of security-sensitive transactions
4. **HIGH_RISK_TABLE_FLAG**: Modifications to critical tables
5. **OTHER_FLAGS**: Additional security events

## API Reference

### Upload File
```
POST /upload
Body: { fileName: string, fileType: "SM20"|"CDHDR"|"CDPOS" }
Response: { uploadUrl: string, analysisId: string }
```

### Start Analysis
```
POST /analyze
Body: { bucket: string, key: string, analysisId: string, fileType: string }
```

### Get Results
```
GET /results/{analysisId}
Response: { status: string, downloadUrl: string, summary: object }
```

## Troubleshooting

### Common Issues

1. **CDK Bootstrap Error**
   ```bash
   cdk bootstrap aws://ACCOUNT-ID/REGION
   ```

2. **Lambda Timeout**
   - Check file size
   - Increase Lambda timeout in CDK stack

3. **CORS Errors**
   - Update API Gateway CORS settings
   - Check CloudFront distribution

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes and test
4. Submit a pull request

## License

Based on SAPAnalyzer3. See repository for license details.

## Support

- GitHub Issues: [https://github.com/polcn/analyzer4/issues](https://github.com/polcn/analyzer4/issues)
- Documentation: See `/docs` folder

---

Built with ❤️ using AWS CDK, React, and Python