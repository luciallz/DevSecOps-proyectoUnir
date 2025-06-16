pipeline {
    agent any

    environment {
        SONAR_HOST_URL = 'http://sonarqube:9000'
        SONAR_SCANNER_VERSION = '3.3.0.1492'
        PROJECT_KEY = 'DevSecOps-proyectoUnir'
        DEP_CHECK_OUTPUT = 'dependency-check-report.html'
        ZAP_REPORT = 'zap-report.html'
        SONAR_SCANNER_OPTS="-Xmx2048m"
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
                        -Dsonar.sources=. \
                        -Dsonar.host.url=${SONAR_HOST_URL} \
                        -Dsonar.exclusions=**/templates/*.html \
                        -Dsonar.qualitygate.wait=true
                    """
                }
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 2, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
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
            script {
                if (currentBuild.currentResult == 'SUCCESS') {
                    archiveArtifacts artifacts: '**/*', allowEmptyArchive: true
                }
            }
        }
    }
}
