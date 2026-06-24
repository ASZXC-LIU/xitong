<template>
  <view class="simple-page">
    <view class="page-header">
      <text class="page-title">货品种类</text>
      <button class="btn btn-sm btn-primary" @click="showForm = true">+ 新增</button>
    </view>
    <view class="form-inline" v-if="showForm">
      <input class="uni-input inline" v-model="form.name" placeholder="种类名称" />
      <input class="uni-input inline" v-model="form.default_unit" placeholder="默认单位" />
      <button class="btn btn-sm btn-primary" @click="save">保存</button>
      <button class="btn btn-sm" @click="showForm=false">取消</button>
    </view>
    <view v-for="item in list" :key="item.id" class="list-item">
      <text class="item-text">{{ item.name }}</text>
      <text class="item-sub">{{ item.default_unit || "" }}</text>
    </view>
    <view v-if="list.length === 0" class="empty-hint">暂无数据</view>
  </view>
</template>

<script>
import { loadCargoTypes, createCargoType } from "../../utils/admin-api"
export default {
  data() { return { list: [], showForm: false, form: { name: "", default_unit: "" } } },
  async onShow() { try { this.list = await loadCargoTypes() } catch(e) { console.error(e) } },
  methods: {
    async save() {
      try { await createCargoType(this.form); this.showForm = false; this.form = { name: "", default_unit: "" }; this.list = await loadCargoTypes() } catch(e) { console.error(e) }
    }
  }
}
</script>

<style>
.simple-page { padding: 12px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.page-title { font-size: 18px; font-weight: 600; }
.form-inline { display: flex; gap: 8px; align-items: center; margin-bottom: 12px; flex-wrap: wrap; background: #fff; border-radius: 8px; padding: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.uni-input.inline { width: auto; flex: 1; min-width: 120px; padding: 6px 10px; border: 1px solid #dcdfe6; border-radius: 4px; font-size: 14px; }
.list-item { display: flex; align-items: center; gap: 12px; background: #fff; border-radius: 8px; padding: 12px 14px; margin-bottom: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.item-text { flex: 1; font-size: 15px; font-weight: 500; }
.item-sub { font-size: 12px; color: #909399; }
.empty-hint { text-align: center; color: #909399; padding: 40px; }
.btn { display: inline-block; padding: 6px 14px; border: 1px solid #dcdfe6; border-radius: 4px; background: #fff; font-size: 13px; }
.btn-primary { background: #409eff; border-color: #409eff; color: #fff; }
.btn-sm { padding: 4px 10px; font-size: 12px; }
</style>
