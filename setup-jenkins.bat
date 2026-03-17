@echo off
REM Jenkins Pipeline Setup Script for Windows
REM Run this batch file to set up Jenkins locally with Docker

setlocal enabledelayedexpansion

echo.
echo ==========================================
echo Jenkins CI/CD Pipeline Setup for Windows
echo ==========================================
echo.

REM Check Docker installation
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not installed or not in PATH
    echo Please install Docker Desktop for Windows first
    echo Download from: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

echo OK: Docker is installed
echo.

REM Create Jenkins home directory
if not exist "%USERPROFILE%\.jenkins" mkdir "%USERPROFILE%\.jenkins"
echo Created Jenkins home directory: %USERPROFILE%\.jenkins

echo.
echo ==========================================
echo Starting Jenkins Server...
echo ==========================================
echo.

REM Check if Jenkins container already exists
docker ps -a | findstr /R "jenkins " >nul
if not errorlevel 1 (
    echo Jenkins container detected. Removing existing container...
    docker stop jenkins 2>nul
    docker rm jenkins 2>nul
)

REM Run Jenkins in Docker on port 8081 (Airflow uses 8080)
docker run ^
    --name jenkins ^
    --detach ^
    --publish 8081:8080 ^
    --publish 50000:50000 ^
    --volume %USERPROFILE%\.jenkins:/var/jenkins_home ^
    --volume //var/run/docker.sock:/var/run/docker.sock ^
    jenkins/jenkins:lts

echo.
echo OK: Jenkins is starting...
echo.
echo ==========================================
echo Initial Setup Instructions
echo ==========================================
echo.
echo 1. Wait 30-60 seconds for Jenkins to fully start
echo.
echo 2. Access Jenkins at: http://localhost:8081  (NOT 8080 - Airflow uses 8080)
echo.
echo 3. Get initial admin password - run this command:
echo    docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
echo.
echo 4. Follow the setup wizard:
echo    - Install suggested plugins
echo    - Create admin user account
echo    - Configure Jenkins URL
echo.
echo ==========================================
echo Required Jenkins Plugins
echo ==========================================
echo.
echo After initial setup, install these plugins:
echo.
echo   1. Pipeline
echo   2. Git
echo   3. GitHub
echo   4. Docker
echo   5. JUnit Plugin
echo   6. HTML Publisher
echo   7. Email Extension
echo   8. Blue Ocean (optional)
echo.
echo To install plugins:
echo   - Go to: Manage Jenkins ^> Plugin Manager
echo   - Search for plugin name
echo   - Click "Install without restart"
echo.
echo ==========================================
echo Create Pipeline Job
echo ==========================================
echo.
echo 1. On Jenkins home page, click "Create a new job"
echo 2. Job name: basel3-regulatory-pipeline
echo 3. Select: Pipeline
echo 4. Click OK
echo.
echo 5. In Pipeline section:
echo    - Definition: Pipeline script from SCM
echo    - SCM: Git
echo    - Repository URL: https://github.com/Techcognize-Inc/DE6-Regulatory-Compliance-Reporting-Pipeline-Basel-III-
echo    - Credentials: Add your GitHub token
echo    - Branch: ^*/main
echo    - Script Path: Jenkinsfile
echo 6. Save
echo.
echo ==========================================
echo GitHub Webhook Configuration
echo ==========================================
echo.
echo 1. Go to your GitHub repository
echo 2. Settings ^> Webhooks ^> Add webhook
echo 3. Payload URL: http://YOUR_JENKINS_IP:8080/github-webhook/
echo 4. Content type: application/json
echo 5. Events: Push events, Pull requests
echo 6. Add webhook
echo.
echo 7. In Jenkins job, enable:
echo    - Build Triggers ^> GitHub hook trigger for GITScm polling
echo.
echo ==========================================
echo Docker Commands
echo ==========================================
echo.
echo View Jenkins logs:
echo   docker logs -f jenkins
echo.
echo Get initial admin password:
echo   docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
echo.
echo Stop Jenkins:
echo   docker stop jenkins
echo.
echo Start Jenkins again:
echo   docker start jenkins
echo.
echo Remove Jenkins container:
echo   docker stop jenkins
echo   docker rm jenkins
echo.
echo ==========================================
echo Setup Complete!
echo ==========================================
echo.
pause
