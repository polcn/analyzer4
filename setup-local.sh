#!/bin/bash

echo "Setting up SAPAnalyzer4 for local development..."

# Backend setup
echo "Setting up backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "Backend setup complete!"

# Frontend setup
echo "Setting up frontend..."
cd ../frontend
npm install
echo "Frontend setup complete!"

# Infrastructure setup
echo "Setting up infrastructure..."
cd ../infrastructure
npm install
echo "Infrastructure setup complete!"

echo ""
echo "Setup complete! To start development:"
echo ""
echo "Backend (in separate terminal):"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  python -m pytest  # Run tests"
echo ""
echo "Frontend (in separate terminal):"
echo "  cd frontend" 
echo "  npm start"
echo ""
echo "Deploy to AWS:"
echo "  cd infrastructure"
echo "  cdk deploy"