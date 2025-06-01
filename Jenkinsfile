pipeline {
    agent any

    stages {
        stage('Clean Workspace') {
            steps {
                deleteDir()   // borra todo el workspace actual antes del checkout
                cleanWs()     // plugin de limpieza (opcional, puedes usar uno u otro)
            }
        }

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup Python') {
            steps {
                sh 'ls -l'  // Verifica que los archivos están después del checkout
                sh 'python3 -m venv venv'
                sh './venv/bin/pip install --upgrade pip'
                sh './venv/bin/pip install -r requirements.txt'
            }
        }

        stage('Run Tests') {
            steps {
                sh './venv/bin/pytest tests/' 
            }
        }

        stage('Run App') {
            steps {
                sh './venv/bin/python app.py &'
                echo 'App started'
            }
        }
    }
}
