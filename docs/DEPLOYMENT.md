# SAPAnalyzer4 Deployment Guide

## Prerequisites

1. **AWS Account** with appropriate permissions (AdministratorAccess or custom policy)
2. **AWS CLI** configured with credentials: `aws configure`
3. **Node.js 18+** and **npm**: [Download](https://nodejs.org/)
4. **Python 3.12+**: [Download](https://www.python.org/)
5. **AWS CDK CLI**: `npm install -g aws-cdk`
6. **Git**: For cloning the repository
7. **Domain** (optional, for custom domain setup)

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

### Custom Domain Setup (GoDaddy)

#### Option 1: Use GoDaddy with Route 53 (Recommended)
1. **Create Route 53 Hosted Zone**:
   ```bash
   aws route53 create-hosted-zone --name yourdomain.com --caller-reference $(date +%s)
   ```

2. **Update GoDaddy Nameservers**:
   - Log into GoDaddy
   - Go to DNS Management
   - Change nameservers to Route 53 NS records

3. **Request ACM Certificate**:
   ```bash
   aws acm request-certificate --domain-name yourdomain.com --validation-method DNS
   ```

4. **Update CDK Stack**:
   ```typescript
   // In sapanalyzer4-stack.ts
   import * as acm from 'aws-cdk-lib/aws-certificatemanager';
   import * as route53 from 'aws-cdk-lib/aws-route53';
   
   const zone = route53.HostedZone.fromLookup(this, 'Zone', {
     domainName: 'yourdomain.com'
   });
   
   const certificate = new acm.Certificate(this, 'Certificate', {
     domainName: 'yourdomain.com',
     validation: acm.CertificateValidation.fromDns(zone),
   });
   
   distribution.addBehavior('/*', new origins.S3Origin(websiteBucket), {
     viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
   });
   ```

#### Option 2: Keep DNS at GoDaddy
1. **Request ACM Certificate** (us-east-1 only for CloudFront)
2. **Add CNAME records** in GoDaddy for validation
3. **After deployment**, add CNAME for CloudFront:
   - Type: CNAME
   - Name: www (or subdomain)
   - Value: [CloudFront-Distribution-URL]

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