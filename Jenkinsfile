pipeline {
    agent any
    environment {
        SONAR_SCANNER_HOME = tool 'SonarQubeScanner'
        PYTHON_VERSION = '3.11'
        FLASK_SECRET_KEY = credentials('FLASK_SECRET_KEY')
    }

    stages {
        stage('Clean Workspace') {
            steps {
                deleteDir()
            }
        }

        stage('Checkout Code') {
            steps {
                checkout scm
            }
        }

        stage('Setup Python') {
            steps {
                sh '''
                rm -rf venv
                python3 -m venv venv
                . venv/bin/activate
                pip install --upgrade pip
                pip install -r requirements.txt
                
                # Verificación de instalación
                pip list | grep -E "flask|pytest|cov"
                '''
            }
        }

        stage('Run Tests with Coverage') {
            steps {
                withEnv(['FLASK_ENV=testing']) {
                    sh '''
                        . venv/bin/activate
                        export PYTHONPATH=$PYTHONPATH:$(pwd)
                        python -m pytest tests/ \
                            --junitxml=test-reports/results.xml \
                            --cov=src \
                            --cov-report=xml:coverage.xml \
                            --cov-report=term-missing \
                            --cov-fail-under=80 -v
                    '''
                }
            }
        }

        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv('SonarQube') {
                    sh """
                    ${SONAR_SCANNER_HOME}/bin/sonar-scanner \
                        -Dsonar.projectKey=DevSecOps-proyectoUnir \
                        -Dsonar.python.version=${PYTHON_VERSION} \
                        -Dsonar.sources=. \
                        -Dsonar.tests=tests \
                        -Dsonar.exclusions=venv/**,**/site-packages/** \
                        -Dsonar.python.coverage.reportPaths=coverage.xml \
                        -Dsonar.python.xunit.reportPath=test-reports/results.xml
                    """
                }
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 30, unit: 'MINUTES') {
                    script {
                        def qg = waitForQualityGate()
                        if (qg.status != 'OK') {
                            echo "Quality Gate status: ${qg.status}"
                            // Continuar pero marcar como inestable
                            currentBuild.result = 'UNSTABLE'
                        }
                    }
                }
            }
        }

        stage('Dependency-Check Analysis') {
            steps {
                script {
                    // Creamos el directorio de salida antes de correr el contenedor
                    sh 'mkdir -p dependency-check-reports'
                }
                // Ejecutamos Dependency-Check dentro del contenedor
                withDockerContainer(image: 'owasp/dependency-check', args: '--entrypoint=""') {
                    sh '''
                        /usr/share/dependency-check/bin/dependency-check.sh \
                            --scan . \
                            --project DevSecOps-proyectoUnir \
                            --out dependency-check-reports \
                            --format HTML \
                            --format XML \
                            --disablePyDist \
                            --disablePyPkg
                    '''
                }
            }
        }

        stage('Build App Docker Image') {
            steps {
                sh 'docker build -f Dockerfile.jenkins -t myapp-image .'
            }
        }

        stage('Run App and DAST with ZAP') {
            steps {
                script {
                    sh 'docker network create zap-net || true'
                    sh 'docker run -d --rm --name myapp --network zap-net -p 5000:5000 myapp-image'
                    
                    docker.image('owasp/zap2docker-stable').inside {
                        sh 'zap-baseline.py -t http://myapp:5000 -r zap-report.html -J zap-report.json -c zap-config.yaml'
                    }
                    
                    sh 'docker stop myapp'
                    sh 'docker network rm zap-net'
                    
                    archiveArtifacts artifacts: 'zap-report.html,zap-report.json'
                }
            }
        }
    }

    post {
        always {
            echo 'Pipeline completed. Cleaning up...'
            sh 'pkill -f "python src/app.py" || echo "No app to kill"'
            archiveArtifacts artifacts: '**/reports/*,**/dependency-check-reports/*,zap-report.*'
            
            // Limpiar workspace (opcional)
            // deleteDir()
        }
        success {
            echo 'Pipeline succeeded!'
        }
        unstable {
            echo 'Pipeline completed with warnings'
        }
        failure {
            echo 'Pipeline failed'
        }
    }
}