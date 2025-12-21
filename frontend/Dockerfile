FROM node:18-alpine

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

# Build the app to check for errors, but for dev we use npm run dev
# RUN npm run build

EXPOSE 3003

CMD ["npm", "run", "dev", "--", "-p", "3003"]
