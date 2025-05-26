# Kehitystila (dev)
FROM node:18-alpine as dev
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev"]

# Tuotantotila (production)
FROM node:18-alpine as production
WORKDIR /app

# Kopioi riippuvuudet ja asenna ne
COPY package*.json ./
RUN npm ci --only=production

# Kopioi lähdekoodi ja buildaa
COPY . .
RUN npm run build

# Poista kehitysriippuvuudet
RUN npm prune --production

EXPOSE 3000

# Käynnistä Next.js tuotannossa
CMD ["npm", "start"]
