<template>
  <view class="simple-page">
    <view class="page-header">
      <text class="page-title">人员管理</text>
      <button class="btn btn-sm btn-primary" @click="showForm = true">+ 新增</button>
    </view>
    <view class="form-inline" v-if="showForm">
      <input class="uni-input inline" v-model="form.display_name" placeholder="姓名" />
      <input class="uni-input inline" v-model="form.phone" type="number" maxlength="11" placeholder="手机号" />
      <input class="uni-input inline" v-model="form.username" placeholder="用户名" />
      <input class="uni-input inline" v-model="form.password" placeholder="密码" type="password" />
      <button class="btn btn-sm btn-primary" @click="save">保存</button>
      <button class="btn btn-sm" @click="showForm=false">取消</button>
    </view>
    <view v-for="item in list" :key="item.id" class="list-item">
      <view class="item-info">
        <text class="item-text">{{ item.display_name }}</text>
        <text class="item-sub">{{ item.username }}</text>
      </view>
      <view class="item-meta">
        <text class="item-phone">{{ item.phone || "--" }}</text>
        <text :class="'item-wx ' + (item.wechat_binded ? 'binded' : 'unbind')">
          {{ item.wechat_binded ? "微信已绑定" : "未绑定" }}
        </text>
      </view>
    </view>
    <view v-if="list.length === 0" class="empty-hint">暂无数据</view>
  </view>
</template>

<script>
import { loadEmployees, createEmployee } from "../../utils/admin-api"
export default {
  data() { return { list: [], showForm: false, form: { display_name: "", phone: "", username: "", password: "" } } },
  async onShow() { try { this.list = await loadEmployees() } catch(e) { console.error(e) } },
  methods: {
    async save() {
      try { await createEmployee(this.form); this.showForm = false; this.form = { display_name: "", phone: "", username: "", password: "" }; this.list = await loadEmployees() } catch(e) { console.error(e) }
    }
  }
}
</script>

<style>
.simple-page { padding: 12px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.page-title { font-size: 18px; font-weight: 600; }
.form-inline { display: flex; gap: 8px; align-items: center; margin-bottom: 12px; flex-wrap: wrap; background: #fff; border-radius: 8px; padding: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.uni-input.inline { width: auto; flex: 1; min-width: 100px; padding: 6px 10px; border: 1px solid #dcdfe6; border-radius: 4px; font-size: 14px; }
.list-item { display: flex; align-items: center; gap: 8px; background: #fff; border-radius: 8px; padding: 12px 14px; margin-bottom: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.item-info { flex: 1; }
.item-text { font-size: 15px; font-weight: 500; display: block; }
.item-sub { font-size: 12px; color: #909399; display: block; margin-top: 2px; }
.item-meta { display: flex; flex-direction: column; align-items: flex-end; gap: 4px; }
.item-phone { font-size: 13px; color: #606266; }
.item-wx { font-size: 11px; padding: 2px 6px; border-radius: 8px; }
.item-wx.binded { background: #f0f9eb; color: #67c23a; }
.item-wx.unbind { background: #f5f5f5; color: #bbb; }
.empty-hint { text-align: center; color: #909399; padding: 40px; }
.btn { display: inline-block; padding: 6px 14px; border: 1px solid #dcdfe6; border-radius: 4px; background: #fff; font-size: 13px; }
</style>
