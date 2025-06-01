pipeline {
    agent any

    stages {
        stage('Clone') {
            steps {
                git 'https://github.com/luciallz/DevSecOps-proyectoUnir/'
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
                // Aquí pondrías comandos para correr tests, si tienes
                // Por ejemplo: sh './venv/bin/python -m unittest discover'
                echo 'No tests defined'
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
