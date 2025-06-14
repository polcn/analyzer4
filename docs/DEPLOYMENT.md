# SAPAnalyzer4 Deployment Guide

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** configured with credentials
3. **Node.js 18+** and **npm**
4. **Python 3.12+**
5. **AWS CDK CLI**: `npm install -g aws-cdk`
6. **Domain** (optional, for custom domain setup)

## Quick Deployment

### 1. Clone and Setup

```bash
cd sapanalyzer4

# Install infrastructure dependencies
cd infrastructure
npm install

# Bootstrap CDK (first time only)
cdk bootstrap
```

### 2. Build Frontend

```bash
cd ../frontend
npm install
npm run build
```

### 3. Deploy to AWS

```bash
cd ../infrastructure
cdk deploy
```

This will:
- Create S3 buckets for data and frontend
- Deploy Lambda functions
- Set up API Gateway
- Create DynamoDB table
- Deploy frontend to CloudFront
- Output URLs for accessing the application

## Configuration

### Environment Variables

Create `.env` files for local development:

**frontend/.env**
```
REACT_APP_API_URL=https://your-api-gateway-url
REACT_APP_S3_BUCKET=sapanalyzer4-data-account-region
```

### Custom Domain Setup

1. **Route 53 Hosted Zone**: Create if not exists
2. **ACM Certificate**: Request certificate for your domain
3. **Update CDK Stack**: Add custom domain configuration

```typescript
// In sapanalyzer4-stack.ts
const customDomain = new apigateway.DomainName(this, 'CustomDomain', {
  domainName: 'api.yourdomain.com',
  certificate: acm.Certificate.fromCertificateArn(this, 'Cert', 'arn:aws:acm:...')
});
```

## Cost Optimization

### Automatic Cost Controls

- Lambda functions scale to zero when idle
- DynamoDB uses on-demand pricing
- S3 lifecycle rules delete old uploads after 30 days
- CloudFront caching reduces bandwidth costs

### Monthly Cost Estimates

- **Idle**: ~$1-2 (S3 + CloudFront)
- **Light usage** (100 analyses): ~$5
- **Medium usage** (1000 analyses): ~$20-30
- **Heavy usage** (10000 analyses): ~$100-150

## Monitoring

### CloudWatch Dashboards

The CDK stack sets up basic monitoring. View in AWS Console:
- Lambda function metrics
- API Gateway requests
- DynamoDB usage
- S3 storage

### Alarms (Optional)

Add CloudWatch alarms for:
- Lambda errors
- API Gateway 4XX/5XX errors
- DynamoDB throttling

## Updates and Maintenance

### Deploy Updates

```bash
# Update backend
cd infrastructure
cdk deploy

# Update frontend only
cd ../frontend
npm run build
cd ../infrastructure
cdk deploy --hotswap
```

### Rollback

```bash
# View deployment history
cdk diff

# Rollback to previous version
# (Redeploy with previous code version)
```

## Cleanup

To remove all resources and avoid charges:

```bash
cd infrastructure
cdk destroy
```

**Warning**: This will delete all data!