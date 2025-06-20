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

        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv('SonarQube') {
                    sh """
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
                    echo "Ejecutando test único src/test_app.py..."
                    ./venv/bin/pytest -p no:warnings src/test_app.py || true
                '''
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

        stage('Publishing OWASP report') {
            steps {
                publishHTML([
                    allowMissing: false,
                    alwaysLinkToLastBuild: true,
                    keepAll: true,
                    reportDir: '.',
                    reportFiles: 'dependency-check-report.html',
                    reportName: 'Reporte OWASP'
                ])
            }
        }

        stage('Start App for DAST') {
            steps {
                sh 'nohup ./venv/bin/python3 src/app.py > app.log 2>&1 &'
                sleep 20
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
                publishHTML([
                    allowMissing: false,
                    alwaysLinkToLastBuild: true,
                    keepAll: true,
                    reportDir: '.',
                    reportFiles: ZAP_REPORT,
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
            script {
                if (currentBuild.currentResult == 'SUCCESS') {
                    archiveArtifacts artifacts: '**/*', allowEmptyArchive: true
                }
            }
        }
    }
}
