# Stage 1: Build React static files
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Stage 2: Serve via Nginx
FROM nginx:alpine
# Change /app/build to /app/dist if using Vite (most modern React apps)
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]