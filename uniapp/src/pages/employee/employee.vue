<template>
  <view class="emp-container">
    <view class="emp-header">
      <button v-if="selectedBatchId" class="btn btn-sm" @click="backToBatches">返回</button>
      <text class="emp-title">{{ selectedBatchId ? batchName : "我的工单" }}</text>
      <view class="emp-user-info">
        <text class="emp-user">{{ user.display_name }}</text>
        <button class="btn btn-sm btn-danger" @click="logout">退出</button>
      </view>
    </view>

    <!-- 批次列表 -->
    <view v-if="!selectedBatchId">
      <view v-if="myBatches.length === 0" class="empty-state">
        <text class="empty-icon">暂无工单</text>
        <text>您还没有被分货货品</text>
      </view>
      <view v-for="b in myBatches" :key="b.id" class="batch-card" @click="selectBatch(b)">
        <view class="batch-card-name">{{ b.name }}</view>
        <view class="batch-card-meta">
          <text>到货: {{ b.arrival_time }}</text>
          <text>货品: {{ b.item_count }} 种</text>
        </view>
        <text class="batch-card-date">{{ b.created_at?.slice(0,10) }}</text>
      </view>
    </view>

    <!-- 货品列表 -->
    <view v-if="selectedBatchId">
      <view v-if="myItems.length === 0" class="empty-state">
        <text class="empty-icon">暂无货品</text>
      </view>
      <view v-for="item in myItems" :key="item.item_id" class="item-card">
        <view class="item-card-header">
          <text class="item-name">{{ item.item_name }}</text>
          <text class="item-unit">{{ item.item_unit }}</text>
          <text :class="'tag ' + statusTag(item)">{{ itemStatusText(item) }}</text>
        </view>
        <view class="item-card-body">
          <view class="info-row">
            <text class="info-label">分货数量</text>
            <text class="info-value">{{ item.allocated_quantity }} {{ item.item_unit }}</text>
          </view>
          <view class="info-row">
            <text class="info-label">报货数量</text>
            <input type="number" :value="item.editQty"
                   step="any" min="0" class="qty-input"
                   @blur="onQtyBlur(item, $event)"
                   @confirm="onQtyConfirm(item, $event)"
                   :placeholder="'输入报货数量 (' + item.item_unit + ')'" />
          </view>
          <view v-if="item.remark" class="info-row">
            <text class="info-label">备注</text>
            <text class="info-value" style="color:#909399">{{ item.remark }}</text>
          </view>
        </view>
        <view class="item-card-footer">
          <button class="btn btn-primary btn-sm" @click="submitItem(item)" :disabled="item.saving">
            {{ item.saving ? "保存中..." : "保存" }}
          </button>
          <text v-if="item.saved" class="save-success">已保存</text>
          <text v-if="item.error" class="save-error">{{ item.error }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { apiGet, apiPost } from '../../utils/request'
import { getStorage, setStorage } from '../../utils/storage'

export default {
  data() {
    return {
      user: {},
      myBatches: [],
      myItems: [],
      selectedBatchId: null,
      batchName: ""
    }
  },
  onShow() {
    this.user = getStorage("user") || {}
    if (!this.user || !this.user.id) {
      uni.navigateTo({ url: "/pages/login/login", redirect: true })
      return
    }
    if (this.selectedBatchId) {
      this.selectBatchById(this.selectedBatchId)
    } else {
      this.loadMyBatches()
    }
  },
  methods: {
    statusTag(item) {
      if (item.actual_quantity != null && Number(item.actual_quantity) > 0) return 'tag-success'
      if (item.allocated_quantity > 0) return 'tag-warning'
      return 'tag-default'
    },
    itemStatusText(item) {
      if (item.actual_quantity != null && Number(item.actual_quantity) > 0) return '已报货'
      if (item.allocated_quantity > 0) return '待报货'
      return '未分配'
    },
    async loadMyBatches() {
      try {
        this.myBatches = await apiGet('/employee/my-batches?user_id=' + this.user.id)
      } catch (e) {
        console.error('loadMyBatches', e)
      }
    },
    async selectBatchById(batchId) {
      try {
        const data = await apiGet('/employee/my-items?user_id=' + this.user.id + '&batch_id=' + batchId)
        this.myItems = data.map(item => ({
          ...item,
          editQty: item.actual_quantity ?? item.allocated_quantity,
          saving: false, saved: false, error: ""
        }))
      } catch (e) {
        console.error('selectBatchById', e)
      }
    },
    selectBatch(b) {
      this.selectedBatchId = b.id
      this.batchName = b.name
      this.selectBatchById(b.id)
    },
    backToBatches() {
      this.selectedBatchId = null
      this.myItems = []
      this.batchName = ""
    },
    onQtyBlur(item, event) {
      item.editQty = Number(event.detail.value) || 0
      this.submitItem(item)
    },
    onQtyConfirm(item, event) {
      item.editQty = Number(event.detail.value) || 0
      this.submitItem(item)
    },
    async submitItem(item) {
      if (item.saving) return
      if (item._timeout) clearTimeout(item._timeout)
      item.saving = true
      item.saved = false
      item.error = ""
      try {
        const payload = {
          assignment_id: item.assignment_id,
          batch_item_id: item.item_id,
          user_id: this.user.id,
          actual_quantity: Number(item.editQty) || 0,
        }
        const data = await apiPost('/employee/submit', payload)
        item.assignment_id = data.assignment_id || item.assignment_id
        item.saved = true
        item.actual_quantity = Number(item.editQty) || 0
        item._timeout = setTimeout(() => { item.saved = false }, 2000)
      } catch (e) {
        item.error = e.message || '网络错误'
      } finally {
        item.saving = false
      }
    },
    logout() {
      setStorage("user", null)
      uni.navigateTo({ url: "/pages/login/login", redirect: true })
    }
  }
}
</script>

<style>
.emp-container { max-width: 600px; margin: 0 auto; padding: 12px; font-size: 14px; }
.emp-header { display: flex; align-items: center; gap: 8px; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid #eee; }
.emp-title { flex: 1; font-size: 18px; font-weight: 600; color: #303133; }
.emp-user-info { display: flex; align-items: center; gap: 8px; }
.emp-user { font-size: 13px; color: #606266; }
.empty-state { text-align: center; padding: 40px 20px; color: #909399; }
.empty-icon { font-size: 18px; margin-bottom: 8px; display: block; }
.batch-card { background: #fff; border-radius: 10px; padding: 14px 16px; margin-bottom: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); border: 1px solid #eee; }
.batch-card-name { font-size: 16px; font-weight: 600; color: #303133; margin-bottom: 6px; }
.batch-card-meta { display: flex; gap: 16px; font-size: 13px; color: #606266; }
.batch-card-date { font-size: 12px; color: #bbb; margin-top: 6px; display: block; }
.item-card { background: #fff; border-radius: 10px; padding: 14px 16px; margin-bottom: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); border: 1px solid #eee; }
.item-card-header { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; padding-bottom: 10px; border-bottom: 1px solid #f0f0f0; }
.item-name { font-size: 16px; font-weight: 600; flex: 1; }
.item-unit { font-size: 12px; color: #909399; }
.item-card-body { margin-bottom: 12px; }
.info-row { display: flex; align-items: center; padding: 6px 0; gap: 8px; }
.info-label { font-size: 13px; color: #909399; min-width: 70px; }
.info-value { font-size: 14px; font-weight: 500; color: #303133; }
.qty-input { flex: 1; max-width: 180px; padding: 8px 10px; border: 1px solid #dcdfe6; border-radius: 6px; font-size: 14px; outline: none; }
.item-card-footer { display: flex; align-items: center; gap: 10px; padding-top: 10px; border-top: 1px solid #f0f0f0; }
.save-success { font-size: 13px; color: #67c23a; }
.save-error { font-size: 13px; color: #f56c6c; }
.tag { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px; }
.tag-success { background: #f0f9eb; color: #67c23a; }
.tag-warning { background: #fdf6ec; color: #e6a23c; }
.tag-default { background: #f0f2f5; color: #909399; }
.btn { display: inline-block; padding: 6px 14px; border: 1px solid #dcdfe6; border-radius: 4px; background: #fff; cursor: pointer; font-size: 13px; }
.btn-primary { background: #409eff; border-color: #409eff; color: #fff; }
.btn-danger { background: #f56c6c; border-color: #f56c6c; color: #fff; }
.btn-sm { padding: 4px 10px; font-size: 12px; }
</style>