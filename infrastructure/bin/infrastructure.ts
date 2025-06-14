#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { SapAnalyzer4Stack } from '../lib/sapanalyzer4-stack';

const app = new cdk.App();
new SapAnalyzer4Stack(app, 'SapAnalyzer4Stack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
});