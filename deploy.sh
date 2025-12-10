#!/bin/bash

# Deployment script for Django Forum
# This script collects static files, creates and applies migrations

echo "🚀 Starting deployment..."
echo ""

# Exit on any error
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color


uv sync


# Step 1: Collect static files
echo -e "${BLUE}📦 Step 1/3: Collecting static files...${NC}"
python manage.py collectstatic --noinput
echo -e "${GREEN}✅ Static files collected${NC}"
echo ""

# Step 2: Create migrations
echo -e "${BLUE}🔨 Step 2/3: Creating migrations...${NC}"
python manage.py makemigrations
echo -e "${GREEN}✅ Migrations created${NC}"
echo ""

# Step 3: Apply migrations
echo -e "${BLUE}🗄️  Step 3/3: Applying migrations...${NC}"
python manage.py migrate
echo -e "${GREEN}✅ Migrations applied${NC}"
echo ""

echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
