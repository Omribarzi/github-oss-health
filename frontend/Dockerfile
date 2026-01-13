FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy application code
COPY . .

# Expose port
EXPOSE 5173

# Run dev server (for production, would use build + serve)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
