# Deployment Guide

Complete guide for deploying InteractiveBook to various platforms.

---

## Table of Contents

1. [Local Deployment](#local-deployment)
2. [Docker Deployment](#docker-deployment)
3. [AWS Deployment](#aws-deployment)
4. [GCP Deployment](#gcp-deployment)
5. [Azure Deployment](#azure-deployment)
6. [Environment Variables](#environment-variables)
7. [CI/CD Pipeline](#cicd-pipeline)
8. [Monitoring & Maintenance](#monitoring--maintenance)

---

## Local Deployment

### Prerequisites
- Python 3.10+
- MongoDB running (Docker or local)
- All dependencies installed

### Steps

1. **Configure environment**
   ```bash
   cd src/assets
   # Edit .env with production values
   ```

2. **Run with production settings**
   ```bash
   cd src
   uvicorn main:app --host 0.0.0.0 --port 5000 --workers 4
   ```

3. **Use a process manager** (recommended)
   - **systemd** (Linux)
   - **PM2** (Node.js process manager for Python)
   - **Supervisor**

---

## Docker Deployment

### Build Docker Image

1. **Create Dockerfile** (if not exists)

   ```dockerfile
   FROM python:3.10-slim

   WORKDIR /app

   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   COPY src/ ./src/

   WORKDIR /app/src

   EXPOSE 5000

   CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
   ```

2. **Build image**
   ```bash
   docker build -t interactivebook:latest .
   ```

3. **Run container**
   ```bash
   docker run -d \
     --name interactivebook \
     -p 5000:5000 \
     -v $(pwd)/src/assets/.env:/app/src/assets/.env \
     interactivebook:latest
   ```

### Docker Compose

1. **Update docker-compose.yml**

   ```yaml
   version: '3.8'

   services:
     mongodb:
       image: mongo:latest
       container_name: mongodb
       ports:
         - "27017:27017"
       volumes:
         - ./mongo-data:/data/db
       networks:
         - backend
       restart: unless-stopped

     app:
       build: .
       container_name: interactivebook
       ports:
         - "5000:5000"
       environment:
         - MONGODB_URl=mongodb://mongodb:27017
       depends_on:
         - mongodb
       networks:
         - backend
       restart: unless-stopped

   networks:
     backend:
   ```

2. **Deploy**
   ```bash
   docker-compose up -d
   ```

---

## AWS Deployment

### Option 1: EC2 Instance

#### Step 1: Launch EC2 Instance

1. **Choose AMI**: Ubuntu 22.04 LTS
2. **Instance Type**: t3.medium or larger
3. **Security Group**: Open ports 22, 80, 443, 5000
4. **Key Pair**: Create/download key pair

#### Step 2: Connect and Setup

```bash
# SSH into instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone repository
git clone https://github.com/yourusername/InteractiveBook.git
cd InteractiveBook
```

#### Step 3: Configure Environment

```bash
cd src/assets
nano .env
# Add production environment variables
```

#### Step 4: Deploy with Docker

```bash
cd docker
docker-compose up -d
```

#### Step 5: Configure Nginx (Reverse Proxy)

```bash
# Install Nginx
sudo apt install nginx -y

# Create configuration
sudo nano /etc/nginx/sites-available/interactivebook
```

Add configuration:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/interactivebook /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### Step 6: SSL with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

### Option 2: ECS (Elastic Container Service)

#### Step 1: Create ECR Repository

```bash
aws ecr create-repository --repository-name interactivebook
```

#### Step 2: Build and Push Image

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin your-account.dkr.ecr.us-east-1.amazonaws.com

# Build image
docker build -t interactivebook .

# Tag image
docker tag interactivebook:latest your-account.dkr.ecr.us-east-1.amazonaws.com/interactivebook:latest

# Push image
docker push your-account.dkr.ecr.us-east-1.amazonaws.com/interactivebook:latest
```

#### Step 3: Create ECS Cluster and Service

Use AWS Console or CLI to create:
- ECS Cluster
- Task Definition
- Service
- Application Load Balancer

### Option 3: Elastic Beanstalk

1. **Install EB CLI**
   ```bash
   pip install awsebcli
   ```

2. **Initialize EB**
   ```bash
   eb init -p python-3.10 interactivebook
   ```

3. **Create environment**
   ```bash
   eb create interactivebook-env
   ```

4. **Deploy**
   ```bash
   eb deploy
   ```

---

## GCP Deployment

### Option 1: Cloud Run

#### Step 1: Build Container Image

```bash
# Set project
gcloud config set project your-project-id

# Build and push to Container Registry
gcloud builds submit --tag gcr.io/your-project-id/interactivebook
```

#### Step 2: Deploy to Cloud Run

```bash
gcloud run deploy interactivebook \
  --image gcr.io/your-project-id/interactivebook \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="MONGODB_URl=your-mongodb-uri,OPENAI_API_KEY=your-key"
```

#### Step 3: Set Up MongoDB Atlas

1. Create MongoDB Atlas cluster
2. Get connection string
3. Update environment variables in Cloud Run

### Option 2: Compute Engine

Similar to AWS EC2 deployment process.

### Option 3: App Engine

1. **Create app.yaml**

   ```yaml
   runtime: python310

   env_variables:
     MONGODB_URl: your-mongodb-uri
     OPENAI_API_KEY: your-key

   handlers:
     - url: /.*
       script: auto
   ```

2. **Deploy**
   ```bash
   gcloud app deploy
   ```

---

## Azure Deployment

### Option 1: Azure Container Instances

```bash
# Create resource group
az group create --name interactivebook-rg --location eastus

# Create container
az container create \
  --resource-group interactivebook-rg \
  --name interactivebook \
  --image your-registry/interactivebook:latest \
  --dns-name-label interactivebook \
  --ports 5000 \
  --environment-variables MONGODB_URl=your-uri OPENAI_API_KEY=your-key
```

### Option 2: Azure App Service

1. **Create App Service**
   ```bash
   az webapp create --resource-group interactivebook-rg --plan myAppServicePlan --name interactivebook --runtime "PYTHON:3.10"
   ```

2. **Configure environment variables**
   ```bash
   az webapp config appsettings set --resource-group interactivebook-rg --name interactivebook --settings MONGODB_URl=your-uri OPENAI_API_KEY=your-key
   ```

3. **Deploy**
   ```bash
   az webapp deployment source config-zip --resource-group interactivebook-rg --name interactivebook --src app.zip
   ```

---

## Environment Variables

### Production Environment Variables

```env
APPLICATION_NAME=InteractiveBook
APP_VERSION=1.0.0
OPENAI_API_KEY=sk-prod-...
FILE_ALLOWED_EXTENSIONS=["application/pdf","text/plain"]
FILE_MAX_SIZE=10485760
FILE_CHUNK_SIZE=512000
MONGODB_URl=mongodb+srv://user:pass@cluster.mongodb.net/
MONGODB_DB_NAME=interactivebook_prod
```

### Security Best Practices

1. **Never commit `.env` files**
2. **Use secrets management**:
   - AWS: Secrets Manager
   - GCP: Secret Manager
   - Azure: Key Vault
3. **Rotate API keys regularly**
4. **Use environment-specific values**
5. **Enable HTTPS only**

---

## CI/CD Pipeline

### GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run tests
        run: |
          pytest tests/
      
      - name: Build Docker image
        run: |
          docker build -t interactivebook:${{ github.sha }} .
      
      - name: Deploy to AWS
        run: |
          # Your deployment commands
          echo "Deploying..."
```

### GitLab CI/CD

Create `.gitlab-ci.yml`:

```yaml
stages:
  - test
  - build
  - deploy

test:
  stage: test
  script:
    - pip install -r requirements.txt
    - pytest tests/

build:
  stage: build
  script:
    - docker build -t interactivebook:$CI_COMMIT_SHA .

deploy:
  stage: deploy
  script:
    - echo "Deploying..."
  only:
    - main
```

---

## Monitoring & Maintenance

### Health Checks

1. **Add health check endpoint** (in `main.py`):
   ```python
   @app.get("/health")
   async def health_check():
       return {"status": "healthy"}
   ```

2. **Configure monitoring**:
   - AWS: CloudWatch
   - GCP: Cloud Monitoring
   - Azure: Application Insights

### Logging

1. **Structured logging**:
   ```python
   import logging
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   )
   ```

2. **Log aggregation**:
   - AWS: CloudWatch Logs
   - GCP: Cloud Logging
   - Azure: Log Analytics

### Backup Strategy

1. **MongoDB Backups**:
   - Daily automated backups
   - Store in S3/GCS/Azure Blob
   - Test restore procedures

2. **File Storage Backups**:
   - Regular snapshots
   - Version control

3. **Configuration Backups**:
   - Version control in Git
   - Encrypted secrets

### Updates

1. **Zero-downtime deployments**:
   - Blue-green deployment
   - Rolling updates
   - Canary releases

2. **Database migrations**:
   - Test migrations in staging
   - Backup before migration
   - Rollback plan

### Performance Monitoring

1. **Metrics to track**:
   - Response time
   - Error rate
   - Request rate
   - Resource usage

2. **Tools**:
   - Prometheus + Grafana
   - Datadog
   - New Relic

---

## Scaling

### Horizontal Scaling

1. **Load Balancer**:
   - AWS: Application Load Balancer
   - GCP: Cloud Load Balancer
   - Azure: Load Balancer

2. **Auto-scaling**:
   - Scale based on CPU/memory
   - Scale based on request rate

### Vertical Scaling

1. **Increase instance size**
2. **Optimize code**
3. **Database optimization**

---

## Security Checklist

- [ ] HTTPS enabled
- [ ] API keys secured
- [ ] Database access restricted
- [ ] Firewall configured
- [ ] Regular security updates
- [ ] DDoS protection
- [ ] Rate limiting enabled
- [ ] Input validation
- [ ] Error message sanitization
- [ ] Logging sensitive data avoided

---

## Troubleshooting

### Common Deployment Issues

1. **Connection refused**
   - Check security groups
   - Verify port configuration
   - Check firewall rules

2. **Environment variables not loading**
   - Verify file path
   - Check file permissions
   - Restart service

3. **Database connection failed**
   - Check connection string
   - Verify network access
   - Check credentials

For more troubleshooting, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

---

## Cost Optimization

1. **Use reserved instances** (AWS)
2. **Right-size instances**
3. **Use spot instances** for non-critical workloads
4. **Optimize database queries**
5. **Use CDN for static assets**
6. **Monitor and alert on costs**

---

For architecture details, see [ARCHITECTURE.md](ARCHITECTURE.md).

