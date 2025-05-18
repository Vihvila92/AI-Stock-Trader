FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
# Kopioi Next.js standalone buildin vaatimat tiedostot juureen
RUN cp -r .next/standalone/* ./ && cp -r .next/static ./
EXPOSE 3000
CMD ["node", "server.js"]
