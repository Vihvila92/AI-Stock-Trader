# Kehitystila (dev)
FROM node:18-bullseye as dev
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev"]

# Tuotantotila (production)
FROM node:18-alpine as production
WORKDIR /app
COPY package*.json ./
RUN npm install --omit=dev
COPY . .
RUN npm run build
RUN cp -r .next/standalone/* ./ && cp -r .next/static ./
EXPOSE 3000
CMD ["node", "server.js"]
