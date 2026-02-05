# EO_XXXXX values are specified in docker-compose.yml

# Docker Official Image
ARG EO_DOCKER_PLAYWRIGHT_IMAGE=mcr.microsoft.com/playwright
ARG EO_DOCKER_PLAYWRIGHT_IMAGE_TAG=noble
FROM ${EO_DOCKER_PLAYWRIGHT_IMAGE}:${EO_DOCKER_PLAYWRIGHT_IMAGE_TAG}

WORKDIR /app

RUN npm init -y && \
    npm install playwright@latest express && \
    npx playwright install --with-deps

COPY server.js .

ENTRYPOINT ["node", "server.js"]

