# Build stage
FROM node:20-alpine AS build
WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
# We can use npm install or ci (assuming lock file exists)
RUN npm install

# Build the app
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
# Copy built assets from builder
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
