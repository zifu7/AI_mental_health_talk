FROM node:22-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
# 国内服务器使用 npmmirror 镜像加速 npm 依赖下载
RUN npm config set registry https://registry.npmmirror.com && npm ci

COPY . .

ARG VITE_FILE_BASE_URL=""
ENV VITE_FILE_BASE_URL=$VITE_FILE_BASE_URL

# Keep the Vite build inside the 2 GB lightweight server memory budget.
ENV NODE_OPTIONS=--max-old-space-size=1536

RUN npm run build

FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
