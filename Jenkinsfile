pipeline {
    agent any
    environment {
        SONAR_SCANNER_HOME = tool 'SonarQubeScanner'
        PYTHON_VERSION = '3.11'
        FLASK_SECRET_KEY = credentials('FLASK_SECRET_KEY')
    }

    stages {
        stage('Clean Workspace') {
            steps { deleteDir() }
        }

        stage('Checkout Code') {
            steps { checkout scm }
        }

        stage('Setup Python') {
            steps {
                sh '''
                    rm -rf venv
                    python3 -m venv venv
                    venv/bin/pip install --upgrade pip
                    venv/bin/pip install -r requirements.txt
                    venv/bin/pip list | grep -E "flask|pytest|cov"
                '''
            }
        }

        stage('Run Tests with Coverage') {
            steps {
                withEnv(['FLASK_ENV=testing']) {
                    sh '''
                        export PYTHONPATH=$PYTHONPATH:$(pwd)
                        mkdir -p test-reports
                        venv/bin/python -m pytest tests/ \
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
                            currentBuild.result = 'UNSTABLE'
                        }
                    }
                }
            }
        }

        stage('Init ODC DB') {
            steps {
                script {
                    def odcDataDir = "${env.WORKSPACE}/odc-data"
                    sh """
                        mkdir -p ${odcDataDir} && chown -R 1000:1000 ${odcDataDir}
                        rm -f ${odcDataDir}/*.lock || true
                    """
                    withCredentials([string(credentialsId: 'nvd-api-key', variable: 'NVD_API_KEY')]) {
                        withDockerContainer(image: 'owasp/dependency-check', args: "--entrypoint='' -v ${odcDataDir}:/usr/share/dependency-check/data -e NVD_API_KEY=${NVD_API_KEY}") {
                            sh '''
                                echo "Actualizando base de datos CVE (una sola vez)..."
                                /usr/share/dependency-check/bin/dependency-check.sh --updateonly --data /usr/share/dependency-check/data --nvdApiKey $NVD_API_KEY || echo "Base ya en uso o actualizada"
                            '''
                        }
                    }
                }
            }
        }

        stage('Dependency-Check Analysis') {
            steps {
                script {
                    def odcDataDir = "${env.WORKSPACE}/odc-data"
                    withDockerContainer(image: 'owasp/dependency-check', args: "--entrypoint='' -v ${odcDataDir}:/usr/share/dependency-check/data") {
                        sh '''
                            /usr/share/dependency-check/bin/dependency-check.sh \
                                --project DevSecOps-proyectoUnir \
                                --scan src \
                                --out dependency-check-reports \
                                --format HTML \
                                --format XML \
                                --disablePyDist \
                                --disablePyPkg \
                                --exclude venv \
                                --exclude .git \
                                --exclude tests \
                                --exclude dist \
                                --exclude build \
                                --noupdate
                        '''
                    }
                }
            }
        }

        stage('Build App Docker Image') {
            steps {
                sh 'docker build -f Dockerfile.jenkins -t myapp-image .'
            }
        }

        stage('Create Docker Network') {
            steps {
                script {
                    def net = sh(script: "docker network ls --filter name=zap-net -q", returnStdout: true).trim()
                    if (!net) {
                        sh "docker network create zap-net"
                    }
                }
            }
        }

        stage('Run App Container') {
            steps {
                script {
                    sh "docker rm -f myapp || true"
                    // Exponer puerto y mapear a host para verificación
                    sh "docker run -d --name myapp --network zap-net -p 5000:5000 myapp-image"
                    
                    // Esperar 15 segundos para que la app inicie completamente
                    sleep 15
                    
                    // Verificar logs de la aplicación
                    sh "docker logs myapp"
                    
                    // Verificar acceso desde el host (temporal para debugging)
                    sh "curl -v http://localhost:5000 || echo 'La aplicación no responde en el host'"
                }
            }
        }

        stage('Verify Network Connectivity') {
            steps {
                script {
                    // Verificar que myapp está accesible desde la red zap-net
                    sh """
                        docker run --rm --network zap-net appropriate/curl \
                        curl -v http://myapp:5000 || echo 'La aplicación no responde dentro de la red zap-net'
                    """
                }
            }
        }

        stage('Run App and DAST with ZAP') {
            steps {
                script {
                    echo "Running ZAP baseline scan on http://myapp:5000"
                    sh """
                        docker run --rm \
                            --network zap-net \
                            -v ${env.WORKSPACE}/zap:/zap/wrk:rw \
                            -e ZAP_LOG_LEVEL=DEBUG \
                            ghcr.io/zaproxy/zaproxy:stable zap-baseline.py \
                            -t http://myapp:5000 \
                            -r /zap/wrk/zap-report.html \
                            -J /zap/wrk/zap-report.json \
                            -d
                    """
                }
            }
            post {
                always {
                    archiveArtifacts artifacts: 'zap/zap-report.html,zap/zap-report.json', allowEmptyArchive: true
                    sh "docker logs myapp > ${env.WORKSPACE}/app.log 2>&1"
                    archiveArtifacts artifacts: 'app.log', allowEmptyArchive: true
                }
            }
        }
    }

    post {
        always {
            echo 'Pipeline completed. Cleaning up...'
        }
        success {
            echo 'Pipeline succeeded!'
        }
        unstable {
            echo 'Pipeline completed with warnings.'
        }
        failure {
            echo 'Pipeline failed.'
        }
    }
}
