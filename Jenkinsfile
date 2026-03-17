pipeline {
    agent any
    
    options {
        buildDiscarder(logRotator(numToKeepStr: '30'))
        timeout(time: 1, unit: 'HOURS')
        timestamps()
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo '========== Checking out code =========='
                checkout scm
            }
        }
        
        stage('Setup Environment') {
            steps {
                echo '========== Setting up Python environment =========='
                sh '''
                    python --version
                    python -m venv venv
                    . venv/bin/activate || venv\\Scripts\\activate.bat
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }
        
        stage('Code Quality') {
            steps {
                echo '========== Running code quality checks =========='
                sh '''
                    . venv/bin/activate || venv\\Scripts\\activate.bat
                    pylint spark_scripts/ --exit-zero --output-format=parseable > pylint-report.txt || true
                    flake8 spark_scripts/ --count --select=E9,F63,F7,F82 --show-source --statistics || true
                '''
            }
        }
        
        stage('Unit Tests') {
            steps {
                echo '========== Running unit tests =========='
                sh '''
                    . venv/bin/activate || venv\\Scripts\\activate.bat
                    python -m pytest Tests/ -v --tb=short --junit-xml=test-results.xml
                '''
            }
        }
        
        stage('Test Report') {
            steps {
                echo '========== Publishing test results =========='
                junit 'test-results.xml'
                publishHTML([
                    reportDir: '.',
                    reportFiles: 'pylint-report.txt',
                    reportName: 'Pylint Report',
                    keepAll: true
                ])
            }
        }
        
        stage('Build Docker Image') {
            when {
                branch 'main'
            }
            steps {
                echo '========== Building Docker image =========='
                sh '''
                    docker build -t basel3-pipeline:${BUILD_NUMBER} .
                    docker tag basel3-pipeline:${BUILD_NUMBER} basel3-pipeline:latest
                '''
            }
        }
        
        stage('Deploy to Staging') {
            when {
                branch 'main'
            }
            steps {
                echo '========== Deploying to staging =========='
                sh '''
                    docker-compose -f docker-compose.yml up -d
                    echo "Application deployed at: http://localhost:8080"
                '''
            }
        }
        
        stage('Health Check') {
            when {
                branch 'main'
            }
            steps {
                echo '========== Running health checks =========='
                sh '''
                    sleep 5
                    curl -f http://localhost:8080/health || echo "Health check failed"
                '''
            }
        }
    }
    
    post {
        always {
            echo '========== Cleaning up =========='
            cleanWs()
        }
        
        success {
            echo '✅ Pipeline succeeded!'
            // Send success notification
            sh '''
                echo "Build ${BUILD_NUMBER} successful" 
            '''
        }
        
        failure {
            echo '❌ Pipeline failed!'
            // Send failure notification
            sh '''
                echo "Build ${BUILD_NUMBER} failed"
            '''
        }
    }
}
