# EO Terraform runner image
# ARGs are set from docker-compose.yml

ARG EO_DOCKER_TERRAFORM_IMAGE=hashicorp/terraform
ARG EO_DOCKER_TERRAFORM_IMAGE_TAG=latest
FROM ${EO_DOCKER_TERRAFORM_IMAGE}:${EO_DOCKER_TERRAFORM_IMAGE_TAG}

# Add customizations here if needed (e.g. extra providers, tools)
# RUN apk add --no-cache curl

WORKDIR /workspace
ENTRYPOINT ["terraform"]
CMD ["--help"]
