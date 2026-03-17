#!/bin/bash
# Jenkins Pipeline Setup Script
# Run this script to quickly set up Jenkins locally with Docker

set -e

echo "=========================================="
echo "Jenkins CI/CD Pipeline Setup"
echo "=========================================="

# Check Docker installation
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

echo "✅ Docker is installed"

# Create Jenkins data directory
JENKINS_HOME="$HOME/.jenkins"
mkdir -p "$JENKINS_HOME"

echo ""
echo "=========================================="
echo "Starting Jenkins Server..."
echo "=========================================="

# Run Jenkins in Docker
docker run \
    --name jenkins \
    --detach \
    --publish 8081:8080 \
    --publish 50000:50000 \
    --volume "$JENKINS_HOME:/var/jenkins_home" \
    --volume /var/run/docker.sock:/var/run/docker.sock \
    jenkins/jenkins:lts

echo ""
echo "✅ Jenkins is starting..."
echo ""
echo "=========================================="
echo "Initial Setup"
echo "=========================================="
echo ""
echo "1. Wait 30-60 seconds for Jenkins to fully start"
echo "2. Access Jenkins at: http://localhost:8081 (NOT 8080 - Airflow uses 8080)"
echo ""
echo "3. Get initial admin password:"
echo "   docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword"
echo ""
echo "4. Install suggested plugins during setup"
echo ""
echo "5. Create admin user and configure"
echo ""
echo "=========================================="
echo "Required Plugins to Install"
echo "=========================================="
echo ""
echo "Go to: Manage Jenkins → Plugin Manager"
echo ""
echo "Search and install:"
echo "  ✓ Pipeline"
echo "  ✓ Git"
echo "  ✓ GitHub"
echo "  ✓ Docker"
echo "  ✓ JUnit Plugin"
echo "  ✓ HTML Publisher"
echo "  ✓ Email Extension"
echo "  ✓ Blue Ocean (optional)"
echo ""
echo "=========================================="
echo "Next Steps"
echo "=========================================="
echo ""
echo "1. Create new Pipeline job:"
echo "   - New Item → basel3-regulatory-pipeline → Pipeline"
echo ""
echo "2. Configure in Pipeline section:"
echo "   - Definition: Pipeline script from SCM"
echo "   - SCM: Git"
echo "   - Repository URL: YOUR_GITHUB_REPO_URL"
echo "   - Script Path: Jenkinsfile"
echo ""
echo "3. Set up GitHub webhook:"
echo "   - GitHub Settings → Webhooks"
echo "   - Payload URL: http://YOUR_JENKINS_IP:8080/github-webhook/"
echo ""
echo "=========================================="
echo "Useful Docker Commands"
echo "=========================================="
echo ""
echo "# View logs"
echo "docker logs -f jenkins"
echo ""
echo "# Get initial password"
echo "docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword"
echo ""
echo "# Stop Jenkins"
echo "docker stop jenkins"
echo ""
echo "# Start Jenkins again"
echo "docker start jenkins"
echo ""
echo "# Remove Jenkins container"
echo "docker rm jenkins  [stop first: docker stop jenkins]"
echo ""
