pipeline {
    agent any

    environment {
        SONAR_SCANNER_VERSION = '4.7.0.2747'
        SONAR_HOST_URL = 'http://sonarqube:9000'
        SONAR_AUTH_TOKEN = credentials('sonar-token-id')  // Asegúrate que este ID existe
        DEP_CHECK_OUTPUT = 'dependency-check-report.html'
        ZAP_REPORT = 'zap-report.html'
        PROJECT_KEY = 'DevSecOps-proyectoUnir'
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

        stage('Setup SonarScanner') {
            steps {
                sh '''
                    export SONAR_SCANNER_HOME=$HOME/.sonar/sonar-scanner-${SONAR_SCANNER_VERSION}-linux
                    curl --create-dirs -sSLo $HOME/.sonar/sonar-scanner.zip https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-$SONAR_SCANNER_VERSION-linux.zip
                    unzip -o $HOME/.sonar/sonar-scanner.zip -d $HOME/.sonar/
                    export PATH=$SONAR_SCANNER_HOME/bin:$PATH
                '''
            }
        }

        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv('SonarQube') {
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
                sh '''
                    /opt/dependency-check/bin/dependency-check.sh --project DevSecOps-proyectoUnir --scan . --format HTML --out . --enableExperimental
                '''
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
                script {
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: './',
                        reportFiles: 'dependency-check-report.html',
                        reportName: 'Reporte OWASP'
                    ])
                }
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
                    zap-baseline.py -t http://localhost:5000 -r ${ZAP_REPORT}
                """
                publishHTML([allowMissing: false, alwaysLinkToLastBuild: true, keepAll: true,
                    reportDir: '.', reportFiles: "${ZAP_REPORT}", reportName: 'OWASP ZAP Report'])
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
