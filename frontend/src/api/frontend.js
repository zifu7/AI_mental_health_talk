import service from "@/utils/request"
//注册接口
export const register = (data) => {
  return service.post("/user/add", data)
}

//创建新对话
export const startSession = (data) => {
  return service.post("/psychological-chat/session/start", data)
}

//获得分页咨询记录
export const getSessionList = (params) => {
  return service.get("/psychological-chat/sessions", { params })
}

//删除咨询话
export const deleteSession = (sessionId) => {
  return service.delete(`/psychological-chat/sessions/${sessionId}`)
}

//获取咨询话详情
export const getSessionDetail = (sessionId) => {
  return service.get(`/psychological-chat/sessions/${sessionId}/messages`)
}

//获取情绪分析结果
export const getEmotionAnalysis = (sessionId) => {
  return service.get(`/psychological-chat/session/${sessionId}/emotion`)
}

//创建情绪日志
export function createEmotionalDiary(data) {
  return service.post("/emotion-diary", data)
}

//获取知识文章列表
export const getKnowledgeList = (params) => {
  return service.get("/knowledge/article/page", { params })
}

///获取知识文章详情
export const getKnowledgeDetail = (id) => {
  return service.get(`/knowledge/article/${id}`)
}
