pipeline {
    agent any

    environment {
        IMAGE_NAME = "sentiment-analysis-api"
        IMAGE_TAG  = "${env.BUILD_NUMBER}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Static Analysis') {
            steps {
                sh '''
                    python -m venv .venv
                    . .venv/bin/activate
                    pip install --quiet flake8
                    flake8 app/ tests/ --max-line-length=120
                '''
            }
        }

        stage('Lint & Unit Tests') {
            steps {
                sh '''
                    python -m venv .venv
                    . .venv/bin/activate
                    pip install --quiet -r requirements.txt
                    pytest tests/ -v
                '''
            }
        }

        stage('Build & Push') {
            steps {
                sh "docker build -t ${IMAGE_NAME}:${IMAGE_TAG} -t ${IMAGE_NAME}:latest ."
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                    docker-compose down --remove-orphans || true
                    IMAGE_TAG=${IMAGE_TAG} docker-compose up -d --build
                '''
            }
        }
    }

    post {
        always {
            sh 'docker system prune -f'
        }
        success {
            echo "Pipeline succeeded – image ${IMAGE_NAME}:${IMAGE_TAG} deployed."
        }
        failure {
            echo "Pipeline failed at stage '${env.STAGE_NAME}'. Check the logs above for details."
        }
    }
}
