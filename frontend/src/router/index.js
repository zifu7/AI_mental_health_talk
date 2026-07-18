import { createRouter, createWebHistory } from "vue-router";
import backendLayout from "@/components/BackendLayout.vue";
import auth from "@/components/AuthorLayout.vue";
import login from "@/views/login.vue";
import register from "@/views/register.vue";
import frontendLayout from "@/components/FrontendLayout.vue";
import home from "@/views/home.vue";
import consultation from "@/views/consultation.vue";
import emotionDiary from "@/views/emotionDiary.vue";
import frontendKnowledge from "@/views/frontendKnowledge.vue";
import articleDetail from "@/views/articleDetail.vue";

const backendRoutes = [
  {
    path: "/back",
    redirect: "/back/dashboard",
    component: backendLayout,
    children: [
      {
        path: "dashboard",
        // ✅ 懒加载大屏模块
        component: () => import("@/views/dashboard.vue"),
        meta: {
          title: "数据分析",
          icon: "PieChart",
        },
      },
      {
        path: "knowledge",
        component: () => import("@/views/knowledge.vue"),
        meta: { title: "知识文章", icon: "ChatLineSquare" },
      },
      {
        path: "consultations",
        component: () => import("@/views/consultations.vue"),
        meta: { title: "咨询记录", icon: "Message" },
      },
      {
        path: "emotional",
        component: () => import("@/views/emotional.vue"),
        meta: { title: "情绪日志", icon: "User" },
      },
    ],
  },
  {
    path: "/auth",
    component: auth,
    meta: {
      title: "用户登录",
    },
    children: [
      {
        path: "login",
        component: login,
        meta: {
          title: "登录",
        },
      },
      {
        path: "register",
        component: register,
        meta: {
          title: "注册",
        },
      },
    ],
  },
];
const frontendRoutes = [
  {
    path: "/",
    component: frontendLayout,
    children: [
      {
        path: "",
        component: home,
      },
      {
        path: "consultation",
        component: consultation,
      },
      {
        path: "emotion-diary",
        component: emotionDiary,
      },
      {
        path: "knowledge",
        component: frontendKnowledge,
      },
      {
        path: "knowledge/article/:id",
        component: articleDetail,
        props: true,
      },
    ],
  },
];
const router = createRouter({
  history: createWebHistory(),
  routes: [...backendRoutes, ...frontendRoutes],
});

//路由前置守卫  在路由跳转的时候触发
router.beforeEach((to, from, next) => {
  //判断是否登录
  const token = localStorage.getItem("token");
  if (token) {
    const userInfo = JSON.parse(localStorage.getItem("userInfo")); //这里为啥要用JSON.parse  将字符串转换为对象
    if (userInfo.user_type === 2) {
      if (to.path.startsWith("/back")) {
        next();
      } else {
        next("/back/dashboard");
      }
    } else {
      if (to.path.startsWith("/back")) {
        next("/auth/login");
      } else {
        next();
      }
    }
  } else {
    if (to.path.startsWith("/back")) {
      //如果在未登录状态下访问后台路由，重定向到登录页
      next("/auth/login");
    } else {
      next();
    }
  }
});
export default router;
