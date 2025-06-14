import * as cdk from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import * as origins from 'aws-cdk-lib/aws-cloudfront-origins';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as s3deploy from 'aws-cdk-lib/aws-s3-deployment';
import { Construct } from 'constructs';
import * as path from 'path';

export class SapAnalyzer4Stack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // S3 Bucket for uploads and results
    const dataBucket = new s3.Bucket(this, 'DataBucket', {
      bucketName: `sapanalyzer4-data-${this.account}-${this.region}`,
      cors: [{
        allowedHeaders: ['*'],
        allowedMethods: [s3.HttpMethods.GET, s3.HttpMethods.PUT, s3.HttpMethods.POST],
        allowedOrigins: ['*'],
        maxAge: 3000,
      }],
      lifecycleRules: [{
        id: 'DeleteOldFiles',
        expiration: cdk.Duration.days(30),
        prefix: 'uploads/',
      }],
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    // DynamoDB table for analysis metadata
    const analysisTable = new dynamodb.Table(this, 'AnalysisTable', {
      tableName: 'sapanalyzer4-analyses',
      partitionKey: { name: 'analysisId', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // Lambda Layer for dependencies
    const dependenciesLayer = new lambda.LayerVersion(this, 'DependenciesLayer', {
      code: lambda.Code.fromAsset(path.join(__dirname, '../../backend'), {
        bundling: {
          image: lambda.Runtime.PYTHON_3_12.bundlingImage,
          command: [
            'bash', '-c',
            'pip install -r requirements.txt -t /asset-output/python && ' +
            'cp -r src/core /asset-output/python/ && ' +
            'cp -r src/data /asset-output/python/'
          ],
        },
      }),
      compatibleRuntimes: [lambda.Runtime.PYTHON_3_12],
      description: 'Dependencies and core modules for SAP Analyzer',
    });

    // Upload Lambda Function
    const uploadFunction = new lambda.Function(this, 'UploadFunction', {
      runtime: lambda.Runtime.PYTHON_3_12,
      code: lambda.Code.fromAsset(path.join(__dirname, '../../backend/src/handlers')),
      handler: 'upload.lambda_handler',
      environment: {
        UPLOAD_BUCKET: dataBucket.bucketName,
      },
      timeout: cdk.Duration.seconds(60),
    });

    // Analysis Lambda Function
    const analyzeFunction = new lambda.Function(this, 'AnalyzeFunction', {
      runtime: lambda.Runtime.PYTHON_3_12,
      code: lambda.Code.fromAsset(path.join(__dirname, '../../backend/src/handlers')),
      handler: 'analyze.lambda_handler',
      layers: [dependenciesLayer],
      environment: {
        UPLOAD_BUCKET: dataBucket.bucketName,
        ANALYSIS_TABLE: analysisTable.tableName,
      },
      timeout: cdk.Duration.minutes(15),
      memorySize: 3008,
    });

    // Get Results Lambda Function
    const getResultsFunction = new lambda.Function(this, 'GetResultsFunction', {
      runtime: lambda.Runtime.PYTHON_3_12,
      code: lambda.Code.fromAsset(path.join(__dirname, '../../backend/src/handlers')),
      handler: 'get_results.lambda_handler',
      environment: {
        UPLOAD_BUCKET: dataBucket.bucketName,
        ANALYSIS_TABLE: analysisTable.tableName,
      },
      timeout: cdk.Duration.seconds(60),
    });

    // Grant permissions
    dataBucket.grantReadWrite(uploadFunction);
    dataBucket.grantReadWrite(analyzeFunction);
    dataBucket.grantRead(getResultsFunction);
    analysisTable.grantReadWriteData(analyzeFunction);
    analysisTable.grantReadData(getResultsFunction);

    // API Gateway
    const api = new apigateway.RestApi(this, 'SapAnalyzer4Api', {
      restApiName: 'SapAnalyzer4 API',
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: apigateway.Cors.ALL_METHODS,
      },
    });

    // API Routes
    const uploadResource = api.root.addResource('upload');
    uploadResource.addMethod('POST', new apigateway.LambdaIntegration(uploadFunction));

    const analyzeResource = api.root.addResource('analyze');
    analyzeResource.addMethod('POST', new apigateway.LambdaIntegration(analyzeFunction));

    const resultsResource = api.root.addResource('results');
    const resultIdResource = resultsResource.addResource('{analysisId}');
    resultIdResource.addMethod('GET', new apigateway.LambdaIntegration(getResultsFunction));

    // Frontend S3 Bucket
    const websiteBucket = new s3.Bucket(this, 'WebsiteBucket', {
      bucketName: `sapanalyzer4-frontend-${this.account}-${this.region}`,
      websiteIndexDocument: 'index.html',
      websiteErrorDocument: 'index.html',
      publicReadAccess: true,
      blockPublicAccess: {
        blockPublicAcls: false,
        blockPublicPolicy: false,
        ignorePublicAcls: false,
        restrictPublicBuckets: false,
      },
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    // CloudFront Distribution
    const distribution = new cloudfront.Distribution(this, 'Distribution', {
      defaultBehavior: {
        origin: new origins.S3Origin(websiteBucket),
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
      },
      defaultRootObject: 'index.html',
      errorResponses: [{
        httpStatus: 404,
        responsePagePath: '/index.html',
        responseHttpStatus: 200,
      }],
    });

    // Deploy frontend
    new s3deploy.BucketDeployment(this, 'DeployWebsite', {
      sources: [s3deploy.Source.asset(path.join(__dirname, '../../frontend/build'))],
      destinationBucket: websiteBucket,
      distribution,
      distributionPaths: ['/*'],
    });

    // Outputs
    new cdk.CfnOutput(this, 'ApiUrl', {
      value: api.url,
      description: 'API Gateway URL',
    });

    new cdk.CfnOutput(this, 'WebsiteUrl', {
      value: distribution.distributionDomainName,
      description: 'CloudFront URL for the website',
    });

    new cdk.CfnOutput(this, 'BucketName', {
      value: dataBucket.bucketName,
      description: 'S3 bucket for uploads and results',
    });
  }
}