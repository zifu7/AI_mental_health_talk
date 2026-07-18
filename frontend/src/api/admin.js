import service from "@/utils/request";

export function login(data) {
  return service.post("/user/login", data);
}

export function categoryTree() {
  return service.get("/knowledge/category/tree");
}
//有多个Query参数，又是axios的get请求，所以要使用params参数???
export function articlePage(params) {
  return service.get("/knowledge/article/page", { params });
}

export const uploadFile = (file, businessId) => {
  const formData = new FormData();
  formData.append("file", file);

  return service.post("/knowledge/file/upload", formData, {
    params: {
      business_type: "article", // 固定值，表示上传的是文章相关图片
      business_id: businessId, // 前端生成的随机 ID
      business_field: "cover_image", // 固定值，表示这是封面图
    },
  });
};
export function createArticle(data) {
  return service.post("/knowledge/article", data);
}

export function getArticle(id) {
  return service.get(`/knowledge/article/${id}`);
}

export function updateArticle(data, id) {
  return service.put(`/knowledge/article/${id}`, data);
}

export const changeArticleStatus = (id, status) => {
  return service.put(`/knowledge/article/${id}/status`, null, {
    params: { status },
  });
};

export function deleteArticle(id) {
  return service.delete(`/knowledge/article/${id}`);
}

export function getConsultations(params) {
  return service.get("/psychological-chat/sessions", { params });
}

//获取会话详情
export function getSessionDetail(sessionId) {
  return service.get(`/psychological-chat/sessions/${sessionId}/messages`);
}

//获取情绪日志列表
export function getEmotionalLogs(params) {
  return service.get("/emotion-diary/admin/page", { params });
}

//删除情绪日志
export function deleteEmotionalLog(id) {
  return service.delete(`/emotion-diary/admin/${id}  `);
}

//获取数据分析数据
export function getAnalyticsOverview() {
  return service.get("/data-analytics/overview");
}

//退出登录
export function logout() {
  return service.post("/user/logout");
}
