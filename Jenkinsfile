pipeline {
  agent any
  stages {
    stage('Clean') {
      steps { deleteDir() }
    }
    stage('Checkout') {
      steps {
        git branch: 'main',
            url: 'https://github.com/luciallz/DevSecOps-proyectoUnir.git',
            credentialsId: 'github-token'
      }
    }
    stage('Success') {
      steps {
        echo 'Checkout completado ✅'
      }
    }
  }
}
