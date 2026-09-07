# Build stage
FROM node:18-alpine as builder

WORKDIR /app

COPY package.json ./

RUN npm install

COPY . .

RUN npm run build

# Production stage
FROM node:18-alpine

WORKDIR /app

# Install a simple HTTP server to serve the built files
RUN npm install -g serve

COPY --from=builder /app/dist ./dist

EXPOSE 3000

ENV NODE_ENV=production

CMD ["serve", "-s", "dist", "-l", "3000"]
