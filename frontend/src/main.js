import { createApp } from 'vue'
import 'element-plus/theme-chalk/dark/css-vars.css'  // 导入官方暗黑变量
import './style.css'  // 你自己的全局样式（放在后面，方便覆盖）
import App from './App.vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import router from './router'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import { createPinia } from 'pinia'

const app = createApp(App)
const pinia = createPinia()
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}
app.use(ElementPlus)
app.use(router)
app.use(pinia)
app.mount('#app')
