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
                withEnv(['FLASK_ENV=test']) {
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
                        // Ejecutar análisis con la herramienta configurada globalmente
                        sh '''
                        mkdir -p dependency-check-reports
                        dependency-check \
                            --scan . \
                            --project "DevSecOps-proyectoUnir" \
                            --out dependency-check-reports \
                            --format HTML \
                            --format XML \
                            --disablePyDist \
                            --disablePyPkg
                        '''
                        
                        // Publicar resultados en Jenkins
                        dependencyCheck pattern: 'dependency-check-reports/dependency-check-report.xml'
                        archiveArtifacts artifacts: 'dependency-check-reports/*.html,dependency-check-reports/*.xml'
                        
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