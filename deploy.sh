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

# Synchronize the application
echo -e "${BLUE}🔄 Synchronizing application...${NC}"
pip install -r requirements.txt
echo -e "${GREEN}✅ Application synchronized${NC}"
echo ""

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

# Step 4: Create superuser if not exists
echo -e "${BLUE}👤 Step 4/4: Ensuring superuser exists...${NC}"
python manage.py createsuperuser \
  --noinput \
  --username "$DJANGO_SUPERUSER_USERNAME" \
  --email "$DJANGO_SUPERUSER_EMAIL" \
  || true
echo -e "${GREEN}✅ Superuser ensured${NC}"
echo ""

echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
