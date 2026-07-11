import pytest

BAD_DOCKERFILE = """\
FROM node:20

WORKDIR /app

COPY . .

RUN npm install
RUN npm run build

CMD ["npm", "start"]
"""

GOOD_DOCKERFILE = """\
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM node:20-alpine

WORKDIR /app

RUN adduser -D -u 1000 appuser

COPY package*.json ./
RUN npm ci --omit=dev && npm cache clean --force

COPY --from=builder /app/dist ./dist

USER appuser

HEALTHCHECK CMD wget -q --spider http://localhost:3000/ || exit 1

CMD ["node", "dist/index.js"]
"""

SECRET_DOCKERFILE = """\
FROM alpine:3.19
COPY .env /app/.env
CMD ["sh"]
"""


@pytest.fixture
def bad_dockerfile():
    return BAD_DOCKERFILE


@pytest.fixture
def good_dockerfile():
    return GOOD_DOCKERFILE


@pytest.fixture
def secret_dockerfile():
    return SECRET_DOCKERFILE
