import axios from "axios";
import { ElMessage } from "element-plus";

const service = axios.create({
  baseURL: "/api",
  timeout: 5000,
});

// 请求拦截器
service.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers["Authorization"] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// 响应拦截器
service.interceptors.response.use(
  (response) => {
    const { data, config } = response;
    if (data.code === "200") {
      return data.data;
    }
    if (data.code === "-1") {
      if (!config.url?.includes("/login")) {
        ElMessage.error(data.msg || "登录过期，请重新登录");
        localStorage.removeItem("token");
        localStorage.removeItem("userInfo");
        window.location.href = "/auth/login";
        return;
      } else {
        ElMessage.error(data.msg || "登录过期，请重新登录");
        return Promise.reject("网络请求失败");
      }
    }
    return Promise.reject(data.message || "请求失败");
  },
  (error) => {
    // 处理 HTTP 错误
    if (error.response) {
      const { status, data } = error.response;
      const msg = data?.detail || data?.message || "请求失败";
      if (status === 401) {
        if (!window.location.pathname.includes("/auth/login")) {
          ElMessage.error(msg);
          localStorage.removeItem("token");
          localStorage.removeItem("userInfo");
          window.location.href = "/auth/login";
        } else {
          ElMessage.error(msg);
        }
      } else {
        ElMessage.error(msg);
      }
    } else {
      ElMessage.error("网络连接失败，请检查网络");
    }
    return Promise.reject(error);
  },
);

// 关键：默认导出
export default service;
