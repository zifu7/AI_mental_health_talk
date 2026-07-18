import axios from "axios";
import { ElMessage } from "element-plus";

const service = axios.create({
  baseURL: "/api",
  timeout: 5000,
});

// 请求拦截器（已正确）
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
    return Promise.reject(data.msg);
  },
  (error) => {
    // 新增：处理 HTTP 401
    if (error.response && error.response.status === 401) {
      if (!window.location.pathname.includes("/auth/login")) {
        ElMessage.error("登录已过期，请重新登录");
        localStorage.removeItem("token");
        localStorage.removeItem("userInfo");
        window.location.href = "/auth/login";
      }
    }
    return Promise.reject(error);
  },
);

// 关键：默认导出
export default service;
