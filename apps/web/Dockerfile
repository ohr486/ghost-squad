FROM node:18-alpine

WORKDIR /app

COPY package.json ./
# package-lock.jsonがあればコピーしますが、初期はないので無視

RUN npm install

COPY . .

CMD ["npm", "run", "dev"]
