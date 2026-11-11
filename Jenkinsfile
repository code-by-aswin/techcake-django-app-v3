pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        skipDefaultCheckout(true)
    }

    environment {
        AWS_REGION = 'ap-south-1'
        AWS_ACCOUNT_ID = '359655298245'
        ECR_REPOSITORY = '359655298245.dkr.ecr.ap-south-1.amazonaws.com/techcake-django-app-v3'
        INSTANCE_ID = 'i-0e4b143a2b1a93eb8'
        COMPOSE_DIR = '/home/ec2-user/techcake-django-app-v2'
        HEALTH_URL = 'https://djangov2.tc-2026-0052.nixlabs.in/health'
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm

                script {
                    env.GIT_SHA = sh(
                        script: 'git rev-parse HEAD',
                        returnStdout: true
                    ).trim()

                    env.IMAGE = "${env.ECR_REPOSITORY}:${env.GIT_SHA}"

                    echo "Git commit: ${env.GIT_SHA}"
                    echo "Docker image: ${env.IMAGE}"
                }
            }
        }

        stage('Test') {
            steps {
                sh '''#!/usr/bin/env bash
                    set -euo pipefail

                    docker run --rm \
                      -e DB_ENGINE=sqlite \
                      -v "$WORKSPACE:/app" \
                      -w /app \
                      python:3.12-slim \
                      sh -c "pip install --no-cache-dir -r requirements.txt && python manage.py test"
                '''
            }
        }

        stage('Build') {
            steps {
                sh '''#!/usr/bin/env bash
                    set -euo pipefail

                    docker build \
                      --build-arg APP_VERSION="$GIT_SHA" \
                      -t "$IMAGE" .
                '''
            }
        }

        stage('Scan') {
            steps {
                sh '''#!/usr/bin/env bash
                    set -euo pipefail

                    mkdir -p "$WORKSPACE/trivy-cache"

                    echo "Generating complete Trivy JSON report..."

                    trivy image \
                      --format json \
                      --output trivy-report.json \
                      --severity UNKNOWN,LOW,MEDIUM,HIGH,CRITICAL \
                      --exit-code 0 \
                      --scanners vuln \
                      --no-progress \
                      "$IMAGE"

                    echo "Checking for CRITICAL vulnerabilities..."

                    trivy image \
                      --severity CRITICAL \
                      --exit-code 1 \
                      --scanners vuln \
                      --no-progress \
                      "$IMAGE"
                '''
            }
        }

        stage('Push') {
            when {
                expression {
                    return env.GIT_BRANCH == 'origin/main' ||
                           env.GIT_BRANCH == 'main' ||
                           env.BRANCH_NAME == 'main'
                }
            }

            steps {
                sh '''#!/usr/bin/env bash
                    set -euo pipefail

                    REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

                    echo "Authenticating with Amazon ECR..."

                    aws ecr get-login-password --region "$AWS_REGION" |
                      docker login --username AWS --password-stdin "$REGISTRY"

                    echo "Pushing scanned image..."

                    docker push "$IMAGE"

                    docker logout "$REGISTRY" || true
                '''
            }
        }

        stage('Deploy') {
            when {
                expression {
                    return env.GIT_BRANCH == 'origin/main' ||
                           env.GIT_BRANCH == 'main' ||
                           env.BRANCH_NAME == 'main'
                }
            }

            steps {
                sh '''#!/usr/bin/env bash
                    set -euo pipefail

                    REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

                    run_ssm() {
                        local script="$1"
                        local params command_id invocation status

                        params="$(jq -cn --arg command "$script" \
                          '{commands: [$command]}')"

                        command_id="$(aws ssm send-command \
                          --region "$AWS_REGION" \
                          --instance-ids "$INSTANCE_ID" \
                          --document-name AWS-RunShellScript \
                          --parameters "$params" \
                          --query 'Command.CommandId' \
                          --output text)"

                        echo "SSM command: $command_id" >&2

                        for attempt in $(seq 1 60); do
                            invocation="$(aws ssm get-command-invocation \
                              --region "$AWS_REGION" \
                              --command-id "$command_id" \
                              --instance-id "$INSTANCE_ID" \
                              --output json 2>/dev/null || true)"

                            status="$(jq -r '.Status // empty' \
                              <<< "$invocation" 2>/dev/null || true)"

                            if [[ "$status" == "Success" ]]; then
                                jq -r '.StandardOutputContent // empty' \
                                  <<< "$invocation"
                                return 0
                            fi

                            if [[ "$status" == "Failed" ||
                                  "$status" == "TimedOut" ||
                                  "$status" == "DeliveryTimedOut" ||
                                  "$status" == "ExecutionTimedOut" ||
                                  "$status" == "Cancelled" ]]; then

                                echo "SSM failed: $status" >&2
                                jq -r '.StandardErrorContent // empty' \
                                  <<< "$invocation" >&2
                                return 1
                            fi

                            sleep 5
                        done

                        echo "SSM command timed out" >&2
                        return 1
                    }

                    echo "Identifying previous running image..."

                    previous_image="$(run_ssm \
                      "docker inspect --format='{{.Config.Image}}' techcake-django-app-v2-django-1")"

                    if [[ "$previous_image" != *:* ]]; then
                        echo "Cannot identify previous image: $previous_image" >&2
                        exit 1
                    fi

                    printf '%s\\n' "$previous_image" > previous-image.txt

                    previous_repository="${previous_image%:*}"
                    previous_tag="${previous_image##*:}"

                    echo "Previous image: $previous_image"

                    rollback() {
                        local rollback_script

                        rollback_script="$(printf '%s\\n' \
                          'set -e' \
                          "cd $COMPOSE_DIR" \
                          "IMAGE_REPOSITORY='$previous_repository' IMAGE_TAG='$previous_tag' docker compose up -d --pull never django")"

                        run_ssm "$rollback_script"
                    }

                    deploy_script="$(cat <<REMOTE
                    set -euo pipefail
                    cd $COMPOSE_DIR
                    trap 'docker logout $REGISTRY >/dev/null 2>&1 || true' EXIT
                    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $REGISTRY
                    IMAGE_REPOSITORY='$ECR_REPOSITORY' IMAGE_TAG='$GIT_SHA' docker compose pull django
                    IMAGE_REPOSITORY='$ECR_REPOSITORY' IMAGE_TAG='$GIT_SHA' docker compose up -d django
REMOTE
                    )"

                    if ! run_ssm "$deploy_script"; then
                        echo "Deployment failed. Rolling back..."
                        rollback || echo "WARNING: Rollback command failed."
                        exit 1
                    fi

                    echo "Deployment command completed."
                '''
            }
        }

        stage('Verify') {
            when {
                expression {
                    return env.GIT_BRANCH == 'origin/main' ||
                           env.GIT_BRANCH == 'main' ||
                           env.BRANCH_NAME == 'main'
                }
            }

            steps {
                sh '''#!/usr/bin/env bash
                    set -euo pipefail

                    REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

                    if [[ ! -s previous-image.txt ]]; then
                        echo "Previous image information is missing."
                        exit 1
                    fi

                    previous_image="$(cat previous-image.txt)"
                    previous_repository="${previous_image%:*}"
                    previous_tag="${previous_image##*:}"

                    run_ssm() {
                        local script="$1"
                        local params command_id invocation status

                        params="$(jq -cn --arg command "$script" \
                          '{commands: [$command]}')"

                        command_id="$(aws ssm send-command \
                          --region "$AWS_REGION" \
                          --instance-ids "$INSTANCE_ID" \
                          --document-name AWS-RunShellScript \
                          --parameters "$params" \
                          --query 'Command.CommandId' \
                          --output text)"

                        for attempt in $(seq 1 60); do
                            invocation="$(aws ssm get-command-invocation \
                              --region "$AWS_REGION" \
                              --command-id "$command_id" \
                              --instance-id "$INSTANCE_ID" \
                              --output json 2>/dev/null || true)"

                            status="$(jq -r '.Status // empty' \
                              <<< "$invocation" 2>/dev/null || true)"

                            if [[ "$status" == "Success" ]]; then
                                jq -r '.StandardOutputContent // empty' \
                                  <<< "$invocation"
                                return 0
                            fi

                            if [[ "$status" == "Failed" ||
                                  "$status" == "TimedOut" ||
                                  "$status" == "DeliveryTimedOut" ||
                                  "$status" == "ExecutionTimedOut" ||
                                  "$status" == "Cancelled" ]]; then
                                echo "Rollback SSM failed: $status" >&2
                                return 1
                            fi

                            sleep 5
                        done

                        return 1
                    }

                    rollback() {
                        local script

                        script="$(printf '%s\\n' \
                          'set -e' \
                          "cd $COMPOSE_DIR" \
                          "IMAGE_REPOSITORY='$previous_repository' IMAGE_TAG='$previous_tag' docker compose up -d --pull never django")"

                        echo "Restoring previous image: $previous_image"
                        run_ssm "$script"
                    }

                    body="$(mktemp)"
                    healthy=false

                    for attempt in $(seq 1 18); do
                        http_code="$(curl -sS \
                          --connect-timeout 5 \
                          --max-time 10 \
                          -o "$body" \
                          -w '%{http_code}' \
                          "$HEALTH_URL" || true)"

                        version="$(jq -r '.version // empty' \
                          "$body" 2>/dev/null || true)"

                        echo "Health check $attempt/18: HTTP $http_code, version=${version:-missing}"

                        if [[ "$http_code" == "200" && "$version" == "$GIT_SHA" ]]; then
                            cat "$body"
                            healthy=true
                            break
                        fi

                        sleep 10
                    done

                    rm -f "$body"

                    if [[ "$healthy" != "true" ]]; then
                        echo "Health verification failed. Rolling back..."
                        rollback
                        exit 1
                    fi

                    echo "Deployment verified successfully!"
                '''
            }
        }
    }

    post {
        always {
            script {
                sh '''
                    if [ ! -f trivy-report.json ]; then
                        printf '{"status":"unavailable","reason":"Build or Trivy did not produce a report."}\\n' > trivy-report.json
                    fi
                '''

                archiveArtifacts(
                    artifacts: 'trivy-report.json',
                    allowEmptyArchive: true
                )
            }

            echo 'Pipeline finished.'
        }

        success {
            echo 'All pipeline stages completed successfully.'
        }

        failure {
            echo 'Pipeline failed. Check the failed stage and console output.'
        }
    }
}
