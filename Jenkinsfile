pipeline {
    agent { docker { image 'python:3.5.1' } }

    stages {
        stage('build') {
            steps {
                    sh 'python --version'
                    sh 'pip --version'
            }
        }
        stage('say helo') {
            steps {
                    sh 'echo "hello"'
            }
        }

    }
    post {
        failure {
            mail to: 'elyhude.de@gmail.com',
                 subject: "Failed Pipeline: ${currentBuild.fullDisplayName}",
                 body: "Something is wrong with ${env.BUILD_URL}"
        }
    }
}