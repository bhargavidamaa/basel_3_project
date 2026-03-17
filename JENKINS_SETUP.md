# Jenkins CI/CD Pipeline Setup Guide

## Prerequisites
- Jenkins server installed and running
- Git plugin installed in Jenkins
- Pipeline plugin installed in Jenkins
- Docker installed (for Docker agent setup)

## Step 1: Install Required Jenkins Plugins

Go to **Manage Jenkins → Plugin Manager** and install:

1. **Pipeline** - For declarative/scripted pipelines
2. **Git** - For Git integration
3. **GitHub** - For GitHub integration
4. **Docker** - For Docker builds
5. **JUnit Plugin** - For test reporting
6. **HTML Publisher Plugin** - For HTML reports
7. **Email Extension Plugin** - For email notifications
8. **Blue Ocean** (optional) - For better visualization

**Port Note:** Jenkins runs on **port 8081** (not 8080) to avoid conflicts with Airflow.

```bash
# Command line installation (if preferred)
java -jar jenkins-cli.jar -s http://localhost:8081 install-plugin pipeline github docker junit email-ext
```

## Step 2: Create a New Pipeline Job in Jenkins

1. Click **New Item**
2. Enter job name: `basel3-regulatory-pipeline`
3. Select **Pipeline**
4. Click **OK**

## Step 3: Configure Pipeline Settings

In the **Pipeline** section, select:
- **Pipeline script from SCM** (not "Pipeline script")
- **SCM**: Git
- **Repository URL**: `https://github.com/Techcognize-Inc/DE6-Regulatory-Compliance-Reporting-Pipeline-Basel-III-`
- **Credentials**: Add GitHub credentials (if private repo)
  - Click **Add** → **Jenkins**
  - Kind: **Username with password** (or SSH key)
  - Username: Your GitHub username
  - Password: Your GitHub personal access token
- **Branch Specifier**: `*/main`
- **Script Path**: `Jenkinsfile`

## Step 4: Setup GitHub Webhook for Auto-Trigger

### GitHub Side:
1. Go to your repository: https://github.com/Techcognize-Inc/DE6-Regulatory-Compliance-Reporting-Pipeline-Basel-III-
2. Click **Settings** → **Webhooks**
3. Click **Add webhook**
4. Configure:
   - **Payload URL**: `http://YOUR_JENKINS_IP:8081/github-webhook/` ⚠️ Note: **Port 8081** (not 8080 - Airflow uses 8080)
   - **Content type**: `application/json`
   - **Events**: 
     - ✅ Push events
     - ✅ Pull requests
   - Click **Add webhook**

### Jenkins Side:
1. In your Jenkins job, go to **Configure**
2. Under **Build Triggers**, check:
   - ✅ **GitHub hook trigger for GITScm polling**
3. Save

## Step 5: Add GitHub Credentials to Jenkins

1. Go to **Manage Jenkins → Credentials**
2. Click **(global)** → **Add Credentials**
3. Configure:
   - **Kind**: GitHub App or Username with password
   - **Username**: Your GitHub username
   - **Password/Token**: Your GitHub Personal Access Token
   - **ID**: `github-credentials`
4. Click **Create**

## Step 6: Configure Jenkins to Access Your Repo

In **Manage Jenkins → System Configuration**, under **GitHub**:
- **API URL**: `https://api.github.com`
- **Credentials**: Select the credentials created above
- Test the connection

## Step 7: Manual Pipeline Trigger (First Time)

1. Go to your Jenkins job: `http://YOUR_JENKINS_IP:8081/job/basel3-regulatory-pipeline`
2. Click **Build Now**
3. Monitor the build in **Build History**

## Step 8: Verify Webhook is Working

1. Make a test commit:
   ```bash
   git add .
   git commit -m "Test: Trigger Jenkins pipeline"
   git push org main
   ```

2. Check GitHub webhook delivery:
   - Go to repo → **Settings** → **Webhooks**
   - Click your webhook
   - Check **Recent Deliveries** tab

3. Jenkins should automatically build within 30 seconds

## Pipeline Stages Explained

| Stage | Purpose | Triggers On |
|-------|---------|------------|
| **Checkout** | Clone repository | All branches |
| **Setup Environment** | Create venv, install deps | All branches |
| **Code Quality** | Run pylint, flake8 | All branches |
| **Unit Tests** | Run pytest | All branches |
| **Build Docker** | Build Docker image | `main` branch only |
| **Deploy to Staging** | Deploy application | `main` branch only |
| **Health Check** | Verify deployment | `main` branch only |

## Troubleshooting

### Build Not Triggering from GitHub
- Check webhook delivery in GitHub
- Verify Jenkins URL is accessible from GitHub
- Check Jenkins logs: `Manage Jenkins → System Log`

### Tests Failing in Pipeline
- Ensure Python 3.11 is installed on Jenkins agent
- Check that all dependencies are in `requirements.txt`
- Run tests locally first: `.venv\Scripts\python.exe -m pytest Tests/`

### Docker Build Failing
- Ensure Docker daemon is running
- Check Jenkins user has Docker permissions: `sudo usermod -aG docker jenkins`

## Email Notifications Setup

In Jenkinsfile, add to `post` section:

```groovy
post {
    success {
        emailext (
            subject: "SUCCESS: Pipeline ${env.BUILD_NUMBER}",
            body: "Build succeeded. See details at ${env.BUILD_URL}",
            to: "your-email@company.com"
        )
    }
    failure {
        emailext (
            subject: "FAILURE: Pipeline ${env.BUILD_NUMBER}",
            body: "Build failed. See details at ${env.BUILD_URL}",
            to: "your-email@company.com"
        )
    }
}
```

## Slack Notifications (Optional)

Add to Jenkinsfile:

```groovy
def slackNotify(String message, String color) {
    slackSend(
        channel: '#cicd-notifications',
        color: color,
        message: message
    )
}

// In stages:
post {
    success {
        script { slackNotify("✅ Build ${BUILD_NUMBER} passed", "good") }
    }
    failure {
        script { slackNotify("❌ Build ${BUILD_NUMBER} failed", "danger") }
    }
}
```

## Quick Reference Commands

```bash
# Test Jenkinsfile syntax (requires Jenkins CLI jar)
java -jar jenkins-cli.jar -s http://localhost:8080 declarative-linter < Jenkinsfile

# View Jenkins logs
docker logs jenkins  # if using Docker

# Restart Jenkins
systemctl restart jenkins  # on Linux
```

## Next Steps

1. ✅ Commit Jenkinsfile to repository
2. ✅ Set up Jenkins server (if not already done)
3. ✅ Create pipeline job
4. ✅ Configure GitHub webhook
5. ✅ Make a test commit to trigger pipeline
6. ✅ Monitor build in Jenkins UI

Once setup is complete, any push to `main` branch will automatically:
- Pull latest code
- Run tests
- Build Docker image
- Deploy to staging
- Send notifications
