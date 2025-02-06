# Käytetään Node.js:n LTS-versiota
FROM node:18 AS build

WORKDIR /app

# Kopioidaan riippuvuustiedostot ja asennetaan ne
COPY package.json package-lock.json ./
RUN npm install

# Kopioidaan koko lähdekoodi ja rakennetaan Next.js-sovellus
COPY . .
RUN npm run build

# Käytetään kevyttä Next.js:n omaa palvelinta tuotantotilassa
CMD ["npm", "run", "start"]
