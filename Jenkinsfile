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
        stage('Clean Workspace') {
            steps {
                deleteDir()
            }
        }

        stage('Checkout') {
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: '*/main']],
                    extensions: [],
                    userRemoteConfigs: [[
                        credentialsId: 'github-token',
                        url: 'https://github.com/luciallz/DevSecOps-proyectoUnir.git'
                    ]]
                ])
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

        stage('Run Tests with Coverage') {
            steps {
                sh '''
                    bash -c "source venv/bin/activate && pytest --cov=src --cov-report=xml"
                '''
            }
        }

        stage('SonarQube Analysis') {
            environment {
                scannerHome = tool 'SonarQubeScanner'
            }
            steps {
                withSonarQubeEnv('SonarQube') { 
                    sh """
                        ${scannerHome}/bin/sonar-scanner \
                        -Dsonar.projectKey=${PROJECT_KEY} \
                        -Dsonar.sources=src \
                        -Dsonar.python.coverage.reportPaths=coverage.xml \
                        -Dsonar.inclusions=**/*.py \
                        -Dsonar.exclusions=**/templates/**,**/static/**,**/node_modules/**,**/*.min.js,**/*.test.*,**/__pycache__/**,**/tests/**
                    """
                }
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 25, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Dependency-Check Analysis') {
            steps {
                script {
                    def dcDataDir = '/var/jenkins_home/dependency-check-data'
                    sh "mkdir -p ${dcDataDir}"
                    withCredentials([string(credentialsId: 'nvd-api-key', variable: 'NVD_API_KEY')]) {
                        sh """
                            docker run --rm \
                                -v \$(pwd):/src \
                                -v ${dcDataDir}:/usr/share/dependency-check/data \
                                owasp/dependency-check:latest \
                                --nvdApiKey ${NVD_API_KEY} \
                                --project ${PROJECT_KEY} \
                                --scan /src \
                                --format HTML \
                                --out /src \
                                --enableExperimental
                        """
                    }
                }
            }
        }

        stage('Publish OWASP Dependency-Check Report') {
            steps {
                publishHTML([
                    allowMissing: false,
                    alwaysLinkToLastBuild: true,
                    keepAll: true,
                    reportDir: '.',
                    reportFiles: 'dependency-check-report.html',
                    reportName: 'OWASP Dependency-Check Report'
                ])
            }
        }

        stage('Start App for DAST') {
            steps {
                sh '''
                    nohup ./venv/bin/python3 src/app.py > app.log 2>&1 &
                    sleep 20
                '''
            }
        }

        stage('OWASP ZAP Scan') {
            steps {
                sh """
                    docker run --rm -u root \
                        -v \$(pwd):/zap/wrk \
                        ghcr.io/zaproxy/zaproxy:stable \
                        zap.sh -cmd -autorun /zap/wrk/zap-config.yaml
                """
            }
        }

        stage('Publish OWASP ZAP Report') {
            steps {
                publishHTML([
                    allowMissing: false,
                    alwaysLinkToLastBuild: true,
                    keepAll: true,
                    reportDir: '.',
                    reportFiles: "${ZAP_REPORT}",
                    reportName: 'OWASP ZAP Report'
                ])
            }
        }

        stage('Stop App') {
            steps {
                sh "pkill -f 'python3 src/app.py' || true"
            }
        }
    }

    post {
        always {
            echo 'Pipeline terminada. Puedes revisar los reportes generados.'
            archiveArtifacts artifacts: '**/*', allowEmptyArchive: true
        }
    }
}
