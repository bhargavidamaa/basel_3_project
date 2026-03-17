# Service Port Configuration

## Port Mapping Reference

| Service | Port | Access URL | Status |
|---------|------|-----------|--------|
| **Airflow UI** | 8080 | http://localhost:8080 | ✅ Already running |
| **Jenkins** | 8081 | http://localhost:8081 | 🔧 Configure below |
| **Spark Master** | 4040 | http://localhost:4040 | (Dynamic) |
| **Docker Registry** | 5000 | http://localhost:5000 | (Optional) |

## Environment Setup

### Current Configuration

Your system has:
- ✅ **Airflow** running on port **8080**
- ✅ **Docker daemon** running
- ✅ **Python 3.11**
- ✅ **Git** configured

### Jenkins Configuration

Jenkins has been configured to use **port 8081** to avoid conflicts with Airflow.

All setup scripts automatically use:
```
docker run --publish 8081:8080 ...
```

This means:
- **External port**: 8081 (what you access: http://localhost:8081)
- **Internal container port**: 8080 (Jenkins container's port)

## Docker Compose Configuration

If you want to run everything together, update your `docker-compose.yml`:

```yaml
version: '3.8'

services:
  airflow:
    image: apache/airflow:2.8.1
    ports:
      - "8080:8080"
    environment:
      - AIRFLOW__CORE__DAGS_FOLDER=/usr/local/airflow/dags
    volumes:
      - ./dags:/usr/local/airflow/dags
      - ./data:/data

  jenkins:
    image: jenkins/jenkins:lts
    ports:
      - "8081:8080"
      - "50000:50000"
    volumes:
      - jenkins_home:/var/jenkins_home
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - DOCKER_HOST=unix:///var/run/docker.sock

  spark-master:
    image: bitnami/spark:latest
    ports:
      - "8888:8888"
      - "7077:7077"
    environment:
      - SPARK_MODE=master

volumes:
  jenkins_home:
```

Then start all services:
```bash
docker-compose up -d
```

## Firewall/Network Rules

If Jenkins can't access Git webhooks, ensure:

1. **Port 8081 is open** on your machine
2. **GitHub can reach** `http://YOUR_MACHINE_IP:8081/github-webhook/`
3. **Jenkins agent can reach** git repositories (usually automatic)

## Port Conflict Resolution

If port 8081 is also in use:

```bash
# Find what's using the port
netstat -ano | findstr :8081  # Windows
lsof -i :8081                 # Mac/Linux

# Kill the process
taskkill /PID <PID> /F        # Windows
kill -9 <PID>                 # Mac/Linux

# Or use a different port
docker run --publish 8090:8080 ...
```

## Service Health Check

Verify all services are running:

```bash
# Airflow (should return HTML)
curl http://localhost:8080

# Jenkins (should return HTML)
curl http://localhost:8081

# Docker (should show version)
docker version

# Python
python --version

# Git
git --version
```

## Quick Commands

```bash
# Start Jenkins
docker run -d -p 8081:8080 --name jenkins jenkins/jenkins:lts

# Stop Jenkins
docker stop jenkins

# View Jenkins logs
docker logs -f jenkins

# Restart Jenkins
docker restart jenkins

# Remove Jenkins (keeps data)
docker stop jenkins

# Remove Jenkins completely
docker stop jenkins && docker rm jenkins
```

## Troubleshooting Port Issues

### Port Already in Use

```bash
# Windows
Get-Process -Id (Get-NetTCPConnection -LocalPort 8081).OwningProcess

# Linux/Mac
lsof -i :8081
```

### Connection Refused

- Ensure Docker is running
- Ensure container is still running: `docker ps`
- Check logs: `docker logs jenkins`
- Increase startup time (wait 60+ seconds after `docker run`)

### GitHub Webhook Not Triggering

- Use correct port in webhook URL: `http://YOUR_IP:8081/github-webhook/`
- Ensure Jenkins is accessible from outside (GitHub needs to reach it)
- Check webhook delivery logs in GitHub settings
