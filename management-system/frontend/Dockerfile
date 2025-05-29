# Development mode (dev)
FROM node:18-alpine as dev
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev"]

# Production mode (production)
FROM node:18-alpine as production
WORKDIR /app

# Copy dependencies and install them
COPY package*.json ./
RUN npm ci --only=production

# Copy source code and build
COPY . .
RUN npm run build && npm prune --production

EXPOSE 3000

# Start Next.js in production
CMD ["npm", "start"]
