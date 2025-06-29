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
                timeout(time: 60, unit: 'MINUTES') {
                    script {
                        def odcDataDir = "${env.WORKSPACE}/odc-data"
                        sh """
                            mkdir -p ${odcDataDir} && chown -R 1000:1000 ${odcDataDir}
                            rm -f ${odcDataDir}/write.lock || true
                            rm -f ${odcDataDir}/*.lock || true
                        """
                        withCredentials([string(credentialsId: 'nvd-api-key', variable: 'NVD_API_KEY')]) {
                            withDockerContainer(image: 'owasp/dependency-check', args: "--entrypoint='' -v ${odcDataDir}:/usr/share/dependency-check/data -e NVD_API_KEY=${NVD_API_KEY}") {
                                sh '''
                                    echo "Actualizando base de datos CVE (una sola vez)..."
                                    /usr/share/dependency-check/bin/dependency-check.sh --updateonly --data /usr/share/dependency-check/data --nvdApiKey $NVD_API_KEY || echo "Actualización DB ya en uso o falló, continuando..."
                                '''
                            }
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
                            echo "Ejecutando análisis ODC sin actualizar la base..."
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

        stage('Login to GHCR') {
            steps {
                withCredentials([string(credentialsId: 'GHCR_TOKEN', variable: 'GHCR_TOKEN')]) {
                sh '''
                    echo $GHCR_TOKEN | docker login ghcr.io -u luciallz --password-stdin
                '''
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
                    def networkExists = sh(script: "docker network ls --filter name=zap-net -q", returnStdout: true).trim()
                    if (!networkExists) {
                        echo "Creating docker network zap-net"
                        sh "docker network create zap-net"
                    } else {
                        echo "Docker network zap-net already exists"
                    }
                }
            }
        }

        stage('Run App Container') {
            steps {
                script {
                    sh "docker rm -f myapp || true"
                    sh "docker run -d --name myapp --network zap-net myapp-image"
                }
            }
        }
        
        stage('Cleanup old ZAP data') {
            steps {
                script {
                    sh '''
                        find /tmp/zap-data -mindepth 1 -maxdepth 1 -type d -mtime +1 -exec rm -rf {} +
                    '''
                }
            }
        }

        stage('Run App and DAST with ZAP') {
            steps {
                script {
                    def zapDir = "/tmp/zap-data/${env.BUILD_ID}"
                    sh "mkdir -p ${zapDir}"

                    echo "Running ZAP scan, output in ${zapDir}"
                    sh """
                        docker run --rm \
                            --network zap-net \
                            -v ${zapDir}:/zap/wrk:rw \
                            ghcr.io/zaproxy/zap-automation:0.15.0 \
                            zap.sh -cmd -autorun /zap/wrk/zap-config.yaml
                    """

                    // Copiar sólo el reporte al workspace
                    sh "cp ${zapDir}/zap-report.html ${env.WORKSPACE}/zap-report.html || true"
                }
            }
            post {
                always {
                    archiveArtifacts artifacts: 'zap-report.html', allowEmptyArchive: true
                }
            }
        }

    }

    post {
        always {
            echo 'Pipeline completed. Cleaning up...'
            archiveArtifacts artifacts: 'zap/zap-report.html,zap/zap-report.json', allowEmptyArchive: true
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
