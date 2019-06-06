pipeline {
    agent { docker { image 'python:3.5.1' } }

    // The stage below is attempting to get the latest version of our application code.
    // Since this is a multi-branch project the 'checkout scm' command is used. If you're working with a standard 
    // pipeline project then you can replace this with the regular 'git url:' pipeline command.
    // The 'checkout scm' command will automatically pull down the code from the appropriate branch that triggered this build.
    stages {
        stage('Get Latest Code') {
            git branch: 'master',
                credentialsId: 'f840f96d-c74a-4de0-a852-1e4af1417c3a',
                url: 'ssh://git@github.org:bor1e/regios.git'
        }    
        
        stage('build') {
            steps {
                    sh 'python --version'
                    sh 'pip --version'
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