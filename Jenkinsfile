pipeline {
    agent any

    environment {
        SONAR_HOST_URL = 'http://localhost:9000'
        SONAR_AUTH_TOKEN = credentials('sonar-token-id')  // Token guardado en Jenkins Credentials
        DEP_CHECK_OUTPUT = 'dependency-check-report.html'
        ZAP_REPORT = 'zap-report.html'
        PROJECT_KEY = 'DevSecOps-proyectoUnir'  // Usa este proyecto para sonar-scanner
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
                    export SONAR_SCANNER_VERSION=4.7.0.2747
                    export SONAR_SCANNER_HOME=$HOME/.sonar/sonar-scanner-$SONAR_SCANNER_VERSION-linux
                    mkdir -p $HOME/.sonar
                    curl -sSLo $HOME/.sonar/sonar-scanner.zip https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-$SONAR_SCANNER_VERSION-linux.zip
                    unzip -o $HOME/.sonar/sonar-scanner.zip -d $HOME/.sonar/
                    export PATH=$SONAR_SCANNER_HOME/bin:$PATH
                '''
            }
        }

        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv('SonarQube') {
                    sh """
                        $HOME/.sonar/sonar-scanner-$SONAR_SCANNER_VERSION-linux/bin/sonar-scanner \
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
                    ./venv/bin/pytest tests/ || echo "Tests fallaron, pero continuamos con la pipeline"
                '''
            }
        }

        stage('Dependency-Check Analysis') {
            steps {
                sh '''
                    ./dependency-check/bin/dependency-check.sh --project ${PROJECT_KEY} --scan . --format HTML --out . --enableExperimental
                '''
                publishHTML([allowMissing: false, alwaysLinkToLastBuild: true, keepAll: true,
                    reportDir: '.', reportFiles: DEP_CHECK_OUTPUT, reportName: 'OWASP Dependency-Check Report'])
            }
        }

        stage('Start App for DAST') {
            steps {
                sh './venv/bin/python app.py &'
                sleep 20  // Espera que la app esté arriba
            }
        }

        stage('OWASP ZAP Scan') {
            steps {
                sh """
                    zap-baseline.py -t http://localhost:5000 -r ${ZAP_REPORT}
                """
                publishHTML([allowMissing: false, alwaysLinkToLastBuild: true, keepAll: true,
                    reportDir: '.', reportFiles: ZAP_REPORT, reportName: 'OWASP ZAP Report'])
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
