# Docker Deployment Guide

**Complete guide for deploying the Warehouse AI Tool using Docker.**

---

## ⚡ Super Quick Start

If you just want to get started quickly:

```bash
# 1. Copy environment file
cp .env.example .env

# 2. Edit .env and add your OpenAI API key
nano .env  # Add: OPENAI_API_KEY=sk-proj-your-key-here

# 3. Deploy with helper script
./docker-deploy.sh
```

**Access at:** http://localhost:5001

---

## 📋 Prerequisites

- Docker installed ([Get Docker](https://docs.docker.com/get-docker/))
- Docker Compose installed (included with Docker Desktop)
- OpenAI API key ([Get API Key](https://platform.openai.com/api-keys))

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/AstroDas360/warehouse-ai-tool.git
cd warehouse-ai-tool
```

### 2. Configure Environment Variables

**IMPORTANT:** Create a `.env` file with your OpenAI API key:

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your OpenAI API key
nano .env  # or use any text editor
```

**Minimum required in `.env`:**
```bash
OPENAI_API_KEY=sk-proj-your-actual-api-key-here
```

⚠️ **Without the `.env` file with OPENAI_API_KEY, the container will fail to start!**

### 3. Build and Run

**Option A: Using Docker Compose (Recommended)**

This will start both the application AND a PostgreSQL database:

```bash
docker-compose up -d
```

**Option B: Using Docker Only (External Database)**

If you're using an external PostgreSQL database (e.g., Render, AWS RDS):

1. Update `.env` with your external database credentials
2. Build the image:

```bash
docker build -t warehouse-ai-tool .
```

3. Run the container:

```bash
docker run -d \
  --name warehouse-ai-tool \
  -p 5001:5001 \
  --env-file .env \
  warehouse-ai-tool
```

### 4. Access the Application

Open your browser and navigate to:

```
http://localhost:5001
```

## 🔧 Docker Compose Configuration

### Services

The `docker-compose.yml` defines two services:

1. **app** - The main application (Flask API + Frontend)
2. **db** - PostgreSQL database (optional, can use external DB)

### Using External Database

If you have an existing PostgreSQL database (Render, AWS RDS, etc.):

1. Comment out the `db` service in `docker-compose.yml`
2. Update `.env` with your external database credentials:

```bash
POSTGRES_HOST=your-external-host.render.com
POSTGRES_PORT=5432
POSTGRES_USER=your-external-user
POSTGRES_PASSWORD=your-external-password
POSTGRES_DATABASE=your-external-database
```

3. Remove `depends_on: - db` from the app service

## 📦 Docker Commands

### View Logs

```bash
# All services
docker-compose logs -f

# App only
docker-compose logs -f app

# Database only
docker-compose logs -f db
```

### Stop Services

```bash
docker-compose down
```

### Stop and Remove Volumes (⚠️ Deletes all data)

```bash
docker-compose down -v
```

### Rebuild After Code Changes

```bash
docker-compose up -d --build
```

### Access Container Shell

```bash
# App container
docker exec -it warehouse-ai-tool bash

# Database container
docker exec -it warehouse-ai-db psql -U warehouse_user -d warehouse_ai_db
```

## 🗄️ Database Management

### Import Data to Docker PostgreSQL

1. Copy your SQL dump into the container:

```bash
docker cp vendors_dump.sql warehouse-ai-db:/tmp/
```

2. Import the data:

```bash
docker exec -it warehouse-ai-db psql -U warehouse_user -d warehouse_ai_db -f /tmp/vendors_dump.sql
```

### Backup Database

```bash
docker exec warehouse-ai-db pg_dump -U warehouse_user warehouse_ai_db > backup_$(date +%Y%m%d).sql
```

### Connect to Database

```bash
docker exec -it warehouse-ai-db psql -U warehouse_user -d warehouse_ai_db
```

## 🔍 Troubleshooting

### "OpenAI API key is required" Error

**Error message:**
```
ValueError: OpenAI API key is required. Set OPENAI_API_KEY in .env file
```

**Solution:**
1. **Create .env file** if it doesn't exist:
   ```bash
   cp .env.example .env
   ```

2. **Edit .env and add your API key:**
   ```bash
   OPENAI_API_KEY=sk-proj-your-actual-api-key-here
   ```

3. **Restart the containers:**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

4. **Verify the key is loaded:**
   ```bash
   docker exec warehouse-ai-tool env | grep OPENAI_API_KEY
   ```

⚠️ **Important:** The `.env` file MUST exist in the same directory as `docker-compose.yml` before running `docker-compose up`.

### Container Won't Start

Check logs:
```bash
docker-compose logs app
```

### Database Connection Issues

1. Verify database is running:
```bash
docker ps
```

2. Check database health:
```bash
docker exec warehouse-ai-db pg_isready -U warehouse_user
```

3. Verify environment variables:
```bash
docker exec warehouse-ai-tool env | grep POSTGRES
```

### Port Already in Use

If port 5001 is already in use, change it in `docker-compose.yml`:

```yaml
ports:
  - "8080:5001"  # Maps host port 8080 to container port 5001
```

Then access at `http://localhost:8080`

### Embeddings Cache Issues

The embeddings cache is persisted in a Docker volume. To reset:

```bash
docker-compose down
docker volume rm warehouse-ai-tool_embeddings_data
docker-compose up -d
```

## 🌐 Production Deployment

### Environment Variables

For production, ensure:

```bash
API_DEBUG=False
API_HOST=0.0.0.0
```

### Security Recommendations

1. **Strong Passwords**: Use strong, unique passwords for PostgreSQL
2. **Environment Files**: Never commit `.env` to version control
3. **SSL/TLS**: Use a reverse proxy (nginx, Caddy) with HTTPS
4. **Firewall**: Restrict database port (5432) access
5. **Resource Limits**: Set memory/CPU limits in docker-compose.yml

### Example with Resource Limits

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G
```

### Using Nginx Reverse Proxy

Example nginx configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🏗️ Build Custom Image

### Build for Different Architecture

```bash
# For ARM64 (Apple Silicon, Raspberry Pi)
docker build --platform linux/arm64 -t warehouse-ai-tool:arm64 .

# For AMD64 (Intel/AMD)
docker build --platform linux/amd64 -t warehouse-ai-tool:amd64 .

# Multi-platform
docker buildx build --platform linux/amd64,linux/arm64 -t warehouse-ai-tool:latest .
```

### Push to Docker Hub

```bash
# Tag the image
docker tag warehouse-ai-tool:latest your-username/warehouse-ai-tool:latest

# Push to Docker Hub
docker push your-username/warehouse-ai-tool:latest
```

## 📊 Monitoring

### Health Check

The container includes a health check that runs every 30 seconds:

```bash
docker inspect --format='{{.State.Health.Status}}' warehouse-ai-tool
```

### Container Stats

```bash
docker stats warehouse-ai-tool
```

## 🔄 Updates

To update to the latest version:

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose up -d --build
```

## 📝 Notes

- **Persistent Data**: Database and embeddings are stored in Docker volumes
- **Network**: Services communicate over a bridge network (`warehouse-network`)
- **Ports**: App runs on 5001, PostgreSQL on 5432 (internal)
- **Logs**: All logs are sent to stdout for Docker logging

## 🆘 Support

For issues or questions:
- Check logs: `docker-compose logs -f`
- GitHub Issues: [Create Issue](https://github.com/AstroDas360/warehouse-ai-tool/issues)
- Documentation: See `docs/` folder
