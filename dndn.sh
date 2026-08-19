jq \
  --arg name "api-gateway" \
  --arg image "ffffffffffffffffffffffffffffffffffff" \
  '
  .taskDefinition
  | del(
      .taskDefinitionArn,
      .revision,
      .status,
      .requiresAttributes,
      .compatibilities,
      .registeredAt,
      .registeredBy,
      .deregisteredAt
    )
  | .containerDefinitions |= map(
      if .name == $name then .image = $image else . end
    )
  ' task-definition.json > new-task-definition.json





deploy_staging:
  stage: deploy
  image: amazon/aws-cli:latest
  rules:
    - if: '$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH'
      when: manual
    - when: never
  variables:
    AWS_DEFAULT_REGION: eu-west-3
    ECS_CLUSTER: cloud-design-cluster
    ECS_SERVICE: inventory-service
    ECS_TASK_FAMILY: inventory
    CONTAINER_NAME: inventory
    ECR_REPOSITORY: inventory
  script:
    - export IMAGE_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$ECR_REPOSITORY:$CI_COMMIT_SHA"
    - export TASK_DEF_JSON="task-definition.json"
    - export NEW_TASK_DEF_JSON="new-task-definition.json"

    - aws ecs describe-task-definition \
        --task-definition "$ECS_TASK_FAMILY" \
        --region "$AWS_DEFAULT_REGION" \
        --query taskDefinition \
        > "$TASK_DEF_JSON"

    - |
      jq --arg IMAGE "$IMAGE_URI" --arg NAME "$CONTAINER_NAME" '
        {
          family: .family,
          taskRoleArn: .taskRoleArn,
          executionRoleArn: .executionRoleArn,
          networkMode: .networkMode,
          containerDefinitions: (
            .containerDefinitions
            | map(if .name == $NAME then .image = $IMAGE else . end)
          ),
          volumes: .volumes,
          placementConstraints: .placementConstraints,
          requiresCompatibilities: .requiresCompatibilities,
          cpu: .cpu,
          memory: .memory,
          runtimePlatform: .runtimePlatform,
          ephemeralStorage: .ephemeralStorage,
          pidMode: .pidMode,
          ipcMode: .ipcMode,
          proxyConfiguration: .proxyConfiguration
        }
        | with_entries(select(.value != null))
      ' "$TASK_DEF_JSON" > "$NEW_TASK_DEF_JSON"

    - export TASK_DEF_ARN=$(
        aws ecs register-task-definition \
          --region "$AWS_DEFAULT_REGION" \
          --cli-input-json "file://$NEW_TASK_DEF_JSON" \
          --query 'taskDefinition.taskDefinitionArn' \
          --output text
      )

    - aws ecs update-service \
        --region "$AWS_DEFAULT_REGION" \
        --cluster "$ECS_CLUSTER" \
        --service "$ECS_SERVICE" \
        --task-definition "$TASK_DEF_ARN"

    - aws ecs wait services-stable \
        --region "$AWS_DEFAULT_REGION" \
        --cluster "$ECS_CLUSTER" \
        --services "$ECS_SERVICE"