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
                    // Crear red Docker (por si la app corre fuera)
                    sh 'docker network create zap-net || true'

                    // Levantar app en red zap-net (si se quiere analizar una app en contenedor)
                    sh 'docker run -d --rm --name myapp --network zap-net myapp-image'

                    // Ejecutar ZAP en background (ya instalado en Jenkins)
                    sh '''
                        zap -daemon -host 0.0.0.0 -port 8090 -config api.disablekey=true > /dev/null 2>&1 &
                        sleep 15  # Esperar a que ZAP arranque
                    '''

                    // Lanza escaneo activo usando la API
                    sh '''
                        # Esperar hasta que ZAP esté listo
                        for i in {1..10}; do
                          curl -s http://localhost:8090/JSON/core/view/version/ && break
                          echo "Esperando que ZAP inicie..."
                          sleep 5
                        done

                        # Iniciar escaneo pasivo y activo
                        curl "http://localhost:8090/JSON/core/action/scan/?url=http://myapp:5000"

                        # Esperar a que termine el escaneo activo
                        while [ "$(curl -s http://localhost:8090/JSON/core/view/status/ | jq -r .status)" != "0" ]; do
                          echo "Escaneando..."
                          sleep 10
                        done

                        # Generar reporte
                        curl "http://localhost:8090/OTHER/core/other/htmlreport/" -o zap-report.html
                        curl "http://localhost:8090/OTHER/core/other/jsonreport/" -o zap-report.json
                    '''

                    // Detener contenedor de app y eliminar red
                    sh 'docker stop myapp || true'
                    sh 'docker network rm zap-net || true'

                    // Guardar artefactos
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