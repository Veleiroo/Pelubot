FROM mcr.microsoft.com/playwright:v1.55.0-jammy

WORKDIR /e2e

# Cache deps
COPY e2e/package.json ./package.json
RUN npm install --silent

# Copy tests and config
COPY e2e/playwright.config.js ./playwright.config.js
COPY e2e/tests ./tests

# Playwright browsers are preinstalled on this base image

CMD ["npm", "test"]
