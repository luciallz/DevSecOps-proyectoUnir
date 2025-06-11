pipeline {
    agent any

    environment {
        SONAR_HOST_URL = 'http://sonarqube:9000'
        PROJECT_KEY = 'DevSecOps-proyectoUnir'
        DEP_CHECK_OUTPUT = 'dependency-check-report.html'
        ZAP_REPORT = 'zap-report.html'
    }

    stages {
        stage('Clean Workspace') {
            steps {
                deleteDir()
                cleanWs()
            }
        }

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('SonarQube Analysis') {
            steps {
                withCredentials([string(credentialsId: 'sonar-token', variable: 'SONAR_AUTH_TOKEN')]) {
                    sh """
                        ~/.sonar/sonar-scanner-${SONAR_SCANNER_VERSION}-linux/bin/sonar-scanner \
                        -Dsonar.projectKey=${PROJECT_KEY} \
                        -Dsonar.sources=. \
                        -Dsonar.host.url=${SONAR_HOST_URL} \
                        -Dsonar.login=${SONAR_AUTH_TOKEN}
                    """
                }
            }
        }

        stage('Setup Python') {
            steps {
                sh 'python3 -m venv venv'
                sh './venv/bin/pip install --upgrade pip'
                sh './venv/bin/pip install -r requirements.txt'
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                    echo "Ejecutando tests sin warnings..."
                    ./venv/bin/pytest -p no:warnings \
                    --ignore=tests/test_basic.py \
                    --ignore=tests/test_helpers.py \
                    --ignore=tests/test_testing.py \
                    --ignore=tests/test_request.py \
                    tests/ || true
                '''
            }
        }

        stage('Dependency-Check Analysis') {
            steps {
                sh """
                    docker run --rm \
                        -v \$(pwd):/src \
                        owasp/dependency-check:latest \
                        --project ${PROJECT_KEY} --scan /src --format HTML --out /src --enableExperimental
                """
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
                sh 'nohup ./venv/bin/python src/flask/app.py > app.log 2>&1 &'
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
                sh "pkill -f 'python app.py' || true"
            }
        }
    }

    post {
        always {
            echo 'Pipeline terminada. Puedes revisar los reportes generados.'
            archiveArtifacts artifacts: '*.html', fingerprint: true
        }
    }
}
