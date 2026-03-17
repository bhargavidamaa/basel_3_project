# Advanced Jenkins Configuration Examples

## 1. Multi-Branch Pipeline

Create a `Jenkinsfile.advanced` with support for multiple branches:

```groovy
pipeline {
    agent any
    
    parameters {
        choice(
            name: 'ENVIRONMENT',
            choices: ['dev', 'staging', 'production'],
            description: 'Deployment environment'
        )
        booleanParam(
            name: 'RUN_TESTS',
            defaultValue: true,
            description: 'Run full test suite'
        )
    }
    
    environment {
        REGISTRY = 'docker.io'
        IMAGE_NAME = 'techcognize/basel3-pipeline'
        BRANCH_NAME = "${env.BRANCH_NAME ?: 'main'}"
    }
    
    stages {
        stage('Build') {
            parallel {
                stage('Compile') {
                    steps {
                        sh 'python -m py_compile spark_scripts/*.py'
                    }
                }
                stage('Dependencies') {
                    steps {
                        sh 'python -m pip check'
                    }
                }
            }
        }
        
        stage('Test') {
            when {
                expression { params.RUN_TESTS == true }
            }
            steps {
                sh '''
                    python -m pytest Tests/ -v \
                        --cov=spark_scripts \
                        --cov-report=xml \
                        --junit-xml=test-results.xml
                '''
            }
        }
        
        stage('Analysis') {
            parallel {
                stage('Code Coverage') {
                    steps {
                        step([$class: 'CoberturaPublisher',
                              autoUpdateHealth: false,
                              autoUpdateStability: false,
                              coberturaReportFile: 'coverage.xml',
                              failUnhealthy: false,
                              failUnstable: false,
                              maxNumberOfBuilds: 0,
                              onlyStable: false,
                              sourceEncoding: 'ASCII',
                              zoomCoverageChart: false])
                    }
                }
                stage('SAST') {
                    steps {
                        sh 'bandit -r spark_scripts/ -f json -o bandit-report.json || true'
                    }
                }
            }
        }
        
        stage('Build Image') {
            when {
                branch 'main'
            }
            steps {
                script {
                    sh '''
                        docker build -t ${REGISTRY}/${IMAGE_NAME}:${BUILD_NUMBER} .
                        docker tag ${REGISTRY}/${IMAGE_NAME}:${BUILD_NUMBER} ${REGISTRY}/${IMAGE_NAME}:latest
                    '''
                }
            }
        }
        
        stage('Push Image') {
            when {
                branch 'main'
            }
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: 'docker-hub', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                        sh '''
                            echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin
                            docker push ${REGISTRY}/${IMAGE_NAME}:${BUILD_NUMBER}
                            docker push ${REGISTRY}/${IMAGE_NAME}:latest
                            docker logout
                        '''
                    }
                }
            }
        }
        
        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                script {
                    switch(params.ENVIRONMENT) {
                        case 'dev':
                            sh 'docker-compose -f docker-compose.dev.yml up -d'
                            break
                        case 'staging':
                            sh 'docker-compose -f docker-compose.staging.yml up -d'
                            break
                        case 'production':
                            sh 'docker-compose -f docker-compose.prod.yml up -d'
                            break
                    }
                }
            }
        }
        
        stage('Smoke Tests') {
            steps {
                sh '''
                    sleep 10
                    curl -f http://localhost:8080/health || exit 1
                    python -m pytest Tests/test_benchmarks.py -v
                '''
            }
        }
    }
    
    post {
        always {
            junit 'test-results.xml'
            publishHTML([
                reportDir: 'htmlcov',
                reportFiles: 'index.html',
                reportName: 'Coverage Report',
                keepAll: true
            ])
        }
        success {
            script {
                env.BUILD_STATUS = 'SUCCESS'
                sh 'echo "Build completed successfully"'
            }
        }
        failure {
            script {
                env.BUILD_STATUS = 'FAILURE'
                sh 'echo "Build failed"'
            }
        }
        cleanup {
            cleanWs()
        }
    }
}
```

## 2. Slack Notifications

Add to your Jenkinsfile:

```groovy
def notifySlack(String message, String color) {
    slackSend(
        channel: '#cicd-notifications',
        color: color,
        message: message,
        teamDomain: 'your-workspace',
        token: credentials('slack-token')
    )
}

// In post section:
post {
    always {
        script {
            def emoji = currentBuild.result == 'SUCCESS' ? '✅' : '❌'
            notifySlack(
                "${emoji} Pipeline ${env.BUILD_NUMBER}: ${currentBuild.result}",
                currentBuild.result == 'SUCCESS' ? 'good' : 'danger'
            )
        }
    }
}
```

## 3. Email Notifications

```groovy
post {
    always {
        emailext(
            to: 'team@example.com',
            subject: 'Pipeline ${BUILD_NUMBER}: ${BUILD_STATUS}',
            body: '''
                Build Details:
                - Build Number: ${BUILD_NUMBER}
                - Build Status: ${BUILD_STATUS}
                - Build URL: ${BUILD_URL}
                - Git Commit: ${GIT_COMMIT}
                
                Test Results:
                - Total Tests: ${TEST_COUNTS,var="total"}
                - Passed: ${TEST_COUNTS,var="pass"}
                - Failed: ${TEST_COUNTS,var="fail"}
                
                Logs: ${BUILD_LOG_MULTILINE,maxLines=30}
            ''',
            attachLog: true,
            attachmentsPattern: 'test-results.xml'
        )
    }
}
```

## 4. Authentication with GitHub

In Jenkins Credentials page:

```groovy
// Use in your pipeline:
withCredentials([string(credentialsId: 'github-token', variable: 'GITHUB_TOKEN')]) {
    sh '''
        curl -H "Authorization: token ${GITHUB_TOKEN}" \
             https://api.github.com/repos/Techcognize-Inc/DE6-Regulatory-Compliance-Reporting-Pipeline-Basel-III-
    '''
}
```

## 5. Deployment Strategies

### Blue-Green Deployment

```groovy
stage('Blue-Green Deploy') {
    steps {
        script {
            sh '''
                # Deploy to GREEN
                docker-compose -f docker-compose.green.yml up -d
                
                # Run tests on GREEN
                sleep 30
                curl -f http://localhost:8081/health || exit 1
                
                # Switch traffic to GREEN
                docker-compose -f docker-compose.blue.yml down
                
                # Rename GREEN to BLUE
                mv docker-compose.green.yml docker-compose.blue.yml
            '''
        }
    }
}
```

### Canary Deployment

```groovy
stage('Canary Deploy') {
    steps {
        script {
            sh '''
                # Deploy to 10% of traffic
                kubectl set image deployment/basel3 \
                    app=basel3:${BUILD_NUMBER} \
                    -n production --record
                
                # Monitor for 5 minutes
                sleep 300
                
                # Check metrics
                kubectl get pods -n production
                
                # If OK, full rollout
                kubectl rollout status deployment/basel3 -n production
            '''
        }
    }
}
```

## 6. Scheduled Builds

In Jenkins UI or in Pipeline:

```groovy
triggers {
    // Build every day at 2 AM
    cron('0 2 * * *')
    
    // Poll GitHub every 15 minutes
    pollSCM('H/15 * * * *')
}
```

## 7. Conditional Builds

```groovy
when {
    // Build only on main branch with tag
    tag pattern: "v\\d+\\.\\d+\\.\\d+", comparator: "REGEXP"
}

when {
    // Build only if changelog contains specific text
    changeset pattern: "spark_scripts/.*", comparator: "GLOB"
}

when {
    // Build based on environment variable
    environment name: 'DEPLOY', value: 'true'
}
```

## 8. Matrix Builds (Multi-Python Versions)

```groovy
agent {
    matrix {
        agent any
        axes {
            axis {
                name 'PYTHON_VERSION'
                values '3.9', '3.10', '3.11'
            }
        }
    }
}

stages {
    stage('Test') {
        steps {
            sh '''
                pyenv install ${PYTHON_VERSION}
                pyenv shell ${PYTHON_VERSION}
                python -m pytest Tests/
            '''
        }
    }
}
```
