def installed = fileExists 'bin/activate'

if (!installed) {
    stage("Install Python Virtual Enviroment") {
        sh 'virtualenv --no-site-packages .'
    }
}

pipeline {
    agent { docker { image 'python:3.5.1' } }
    stages {
        stage('build') {
            steps {
                sh 'python --version'
            }
        }
    }
}