pipeline {
    agent any
    tools {
        dependencyCheck 'OWASP Dependency-Check'
    }
    environment {
        SONAR_SCANNER_HOME = tool 'SonarQubeScanner'
        PYTHON_VERSION = '3.11'
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

        stage('Setup Python Environment') {
            steps {
                sh "python${PYTHON_VERSION} -m venv venv"
                sh '. venv/bin/activate && pip install --upgrade pip'
                sh '. venv/bin/activate && pip install -r requirements.txt pytest pytest-cov'
            }
        }

        stage('Run Tests with Coverage') {
            steps {
                sh '''
                . venv/bin/activate
                mkdir -p test-reports
                PYTHONPATH=. pytest tests/ \
                    --junitxml=test-reports/results.xml \
                    --cov=. \
                    --cov-report=xml:coverage.xml \
                    -v
                '''
            }
        }

        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv('SonarQube') {
                    sh """
                    ${SONAR_SCANNER_HOME}/bin/sonar-scanner \
                        -Dsonar.projectKey=DevSecOps-proyectoUnir \
                        -Dsonar.python.version=${PYTHON_VERSION} \
                        -Dsonar.sources=src \
                        -Dsonar.tests=tests \
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
                    try {
                        // Instalar Dependency-Check si no existe
                        sh '''
                        if [ ! -f /opt/dependency-check/bin/dependency-check.sh ]; then
                            echo "Instalando OWASP Dependency-Check..."
                            sudo mkdir -p /opt/dependency-check
                            sudo wget -q -O /tmp/dc.zip https://github.com/jeremylong/DependencyCheck/releases/latest/download/dependency-check-release.zip
                            sudo unzip -j /tmp/dc.zip "dependency-check/bin/*" -d /opt/dependency-check/bin/
                            sudo unzip -j /tmp/dc.zip "dependency-check/lib/*" -d /opt/dependency-check/lib/
                            sudo chmod +x /opt/dependency-check/bin/dependency-check.sh
                            sudo rm /tmp/dc.zip
                        fi
                        '''
                        
                        // Ejecutar análisis
                        sh '''
                        mkdir -p dependency-check-reports
                        /opt/dependency-check/bin/dependency-check.sh \
                            --scan . \
                            --format HTML \
                            --format XML \
                            --out dependency-check-reports/ \
                            --disableAssembly
                        '''
                        
                        // Publicar resultados
                        dependencyCheck pattern: 'dependency-check-reports/dependency-check-report.xml'
                        archiveArtifacts artifacts: 'dependency-check-reports/*'
                        
                    } catch (Exception e) {
                        echo "Error en Dependency-Check: ${e.toString()}"
                        currentBuild.result = 'UNSTABLE'
                    }
                }
            }
        }
        stage('DAST with OWASP ZAP') {
            steps {
                script {
                    try {
                        sh '. venv/bin/activate && python app.py &'
                        echo "Waiting for app to start..."
                        sleep 30
                        
                        sh 'zap-baseline.py -t http://localhost:5000 -r zap-report.html -J zap-report.json -c zap-config.yaml'
                        
                        // Publicar reportes
                        archiveArtifacts artifacts: 'zap-report.html,zap-report.json'
                    } catch (e) {
                        echo "ZAP scan failed: ${e}"
                        currentBuild.result = 'UNSTABLE'
                    } finally {
                        sh 'pkill -f "python app.py" || echo "App not running"'
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