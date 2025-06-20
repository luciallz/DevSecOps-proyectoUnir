pipeline {
    agent any

    environment {
        SONAR_HOST_URL = 'http://sonarqube:9000'
        SONAR_SCANNER_VERSION = '3.3.0.1492'
        PROJECT_KEY = 'DevSecOps-proyectoUnir'
        DEP_CHECK_OUTPUT = 'dependency-check-report.html'
        ZAP_REPORT = 'zap-report.html'
        SONAR_SCANNER_OPTS = "-Xmx2048m"
    }

    stages {
        stage('Clean Workspace') { steps { deleteDir() } }

        stage('Checkout') { 
            steps {
                checkout scm: [
                    $class: 'GitSCM', 
                    branches: [[name: '*/main']], 
                    userRemoteConfigs: [[
                        credentialsId: 'github-token', 
                        url: 'https://github.com/luciallz/DevSecOps-proyectoUnir.git'
                    ]]
                ]
            }
        }

        stage('Setup Python Virtual Environment') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                    . venv/bin/activate
                    echo "Ejecutando test con cobertura..."
                    pytest --cov=src --cov-report=xml src/tests/
                '''
            }
        }

        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv('SonarQube') {
                    sh '''
                        . venv/bin/activate
                        ${tool 'SonarQubeScanner'}/bin/sonar-scanner \
                        -Dsonar.projectKey=${PROJECT_KEY} \
                        -Dsonar.sources=src \
                        -Dsonar.tests=src/tests \
                        -Dsonar.inclusions=src/**/*.py \
                        -Dsonar.test.inclusions=src/tests/**/*.py \
                        -Dsonar.exclusions=**/templates/**,**/static/**,**/node_modules/**,**/*.min.js,**/*.test.*,**/__pycache__/** \
                        -Dsonar.coverageReportPaths=coverage.xml \
                        -Dsonar.python.version=3 \
                        -Dsonar.qualitygate.wait=true
                    '''
                }
            }
        }

        // ... resto de etapas igual ...

    }

    post {
        always {
            echo 'Pipeline terminada. Puedes revisar los reportes generados.'
            script {
                if (currentBuild.currentResult == 'SUCCESS') {
                    archiveArtifacts artifacts: '**/*', allowEmptyArchive: true
                }
            }
        }
    }
}
pipeline {
    agent any

    environment {
        SONAR_HOST_URL = 'http://sonarqube:9000'
        SONAR_SCANNER_VERSION = '3.3.0.1492'
        PROJECT_KEY = 'DevSecOps-proyectoUnir'
        DEP_CHECK_OUTPUT = 'dependency-check-report.html'
        ZAP_REPORT = 'zap-report.html'
        SONAR_SCANNER_OPTS = "-Xmx2048m"
    }

    stages {
        stage('Clean Workspace') { steps { deleteDir() } }

        stage('Checkout') { 
            steps {
                checkout scm: [
                    $class: 'GitSCM', 
                    branches: [[name: '*/main']], 
                    userRemoteConfigs: [[
                        credentialsId: 'github-token', 
                        url: 'https://github.com/luciallz/DevSecOps-proyectoUnir.git'
                    ]]
                ]
            }
        }

        stage('Setup Python Virtual Environment') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                    . venv/bin/activate
                    echo "Ejecutando test con cobertura..."
                    pytest --cov=src --cov-report=xml src/tests/
                '''
            }
        }

        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv('SonarQube') {
                    sh '''
                        . venv/bin/activate
                        ${tool 'SonarQubeScanner'}/bin/sonar-scanner \
                        -Dsonar.projectKey=${PROJECT_KEY} \
                        -Dsonar.sources=src \
                        -Dsonar.tests=src/tests \
                        -Dsonar.inclusions=src/**/*.py \
                        -Dsonar.test.inclusions=src/tests/**/*.py \
                        -Dsonar.exclusions=**/templates/**,**/static/**,**/node_modules/**,**/*.min.js,**/*.test.*,**/__pycache__/** \
                        -Dsonar.coverageReportPaths=coverage.xml \
                        -Dsonar.python.version=3 \
                        -Dsonar.qualitygate.wait=true
                    '''
                }
            }
        }

        // ... resto de etapas igual ...

    }

    post {
        always {
            echo 'Pipeline terminada. Puedes revisar los reportes generados.'
            script {
                if (currentBuild.currentResult == 'SUCCESS') {
                    archiveArtifacts artifacts: '**/*', allowEmptyArchive: true
                }
            }
        }
    }
}
