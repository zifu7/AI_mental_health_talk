<template>
 <el-form :model="formData" ref="ruleFormRef">
  <el-row :gutter="24">
     <template v-for="item in formItemAttrs" :key="item.prop">  
        <el-col v-bind="item.col">
      <el-form-item :label="item.label" :prop="item.prop" >
        <component :is="isCamp(item.comp)"  :placeholder="item.placeholder" v-model="formData[item.prop]">
        <template v-if="item.comp==='select'">
          <el-option label="全部" value=""/>
          <el-option v-for="opt in item.options" :key="opt.value" :label="opt.label" :value="opt.value"/>
        </template>
        </component>
      </el-form-item> 
       </el-col>
  </template>

  </el-row>
 <el-row >
    <el-button type="primary" @click="handleSearch">查询</el-button>
  <el-button  @click="handleReset">重置</el-button>
 </el-row>

 </el-form>
</template>
<script setup>
import { ref ,reactive,computed} from 'vue'
const props = defineProps({
  formItem: {
    type: Array,
    default: () => []
  }
})
const isCamp = (camp)=>{
  return {
    input:"elInput",
    select:"elSelect",
  }[camp]
}
const formData = reactive({})
const emit = defineEmits(["search"])
const handleSearch = () => {
emit("search",formData)
}
const ruleFormRef = ref()
const handleReset = () => {
  if(!ruleFormRef.value) return
  ruleFormRef.value.resetFields()
}
const formItemAttrs = computed(()=>{
const {formItem} = props
formItem.forEach(item => {item.col = {xs:24,sm:12,md:8,lg:6,xl:4}
})
return formItem
}
) 


</script>

