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
                parallel(
                    one: {
                        echo "I'm on the first branch!"
                    },
                    two: {
                        echo "I'm on the second branch!"
                    },
                    three: {
                       echo "I'm on the third branch!"
                       echo "But you probably guessed that already."
                    }
                )
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