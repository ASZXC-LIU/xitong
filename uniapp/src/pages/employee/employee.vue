<template>
  <view class="emp-page">
    <view class="emp-header">
      <button v-if="selectedBatchId" class="btn btn-sm" @click="backToBatches">返回</button>
      <text class="emp-title">{{ selectedBatchId ? batchName : '我的工单' }}</text>
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

    <!-- 货品列表（表格） -->
    <view v-if="selectedBatchId" class="table-wrap">
      <view class="table-toolbar">
        <text class="table-info">{{ batchName }} - 共 {{ myItems.length }} 种货品</text>
      </view>
      <view v-if="myItems.length === 0" class="empty-state">
        <text class="empty-icon">暂无货品</text>
      </view>
      <view v-else class="matrix-table-wrap">
        <view class="emp-table" style="display:table;width:100%;border-collapse:collapse;font-size:13px;min-width:500px">
          <!-- thead -->
          <view style="display:table-header-group">
            <view style="display:table-row">
              <view style="display:table-cell;padding:8px 6px;border-bottom:2px solid #000;text-align:center;font-weight:700;font-size:12px;background:#d9e1f2;color:#333;white-space:nowrap">货品名称</view>
              <view style="display:table-cell;padding:8px 6px;border-bottom:2px solid #000;text-align:center;font-weight:700;font-size:12px;background:#d9e1f2;color:#333;white-space:nowrap">单位</view>
              <view style="display:table-cell;padding:8px 6px;border-bottom:2px solid #000;text-align:center;font-weight:700;font-size:12px;background:#d9e1f2;color:#333;white-space:nowrap">分货数量</view>
              <view style="display:table-cell;padding:8px 6px;border-bottom:2px solid #000;text-align:center;font-weight:700;font-size:12px;background:#d9e1f2;color:#333;white-space:nowrap">报货数量</view>
              <view style="display:table-cell;padding:8px 6px;border-bottom:2px solid #000;text-align:center;font-weight:700;font-size:12px;background:#d9e1f2;color:#333;white-space:nowrap">状态</view>
              <view style="display:table-cell;padding:8px 6px;border-bottom:2px solid #000;text-align:center;font-weight:700;font-size:12px;background:#d9e1f2;color:#333;white-space:nowrap">操作</view>
            </view>
          </view>
          <!-- tbody -->
          <view style="display:table-row-group">
            <view v-for="item in myItems" :key="item.item_id" style="display:table-row">
              <view style="display:table-cell;padding:6px 4px;border-bottom:1px solid #e0e0e0;text-align:left;font-weight:500;padding-left:10px;white-space:nowrap">
                <text>{{ item.item_name }}</text>
              </view>
              <view style="display:table-cell;padding:6px 4px;border-bottom:1px solid #e0e0e0;text-align:center;color:#909399;font-size:12px">
                <text>{{ item.item_unit }}</text>
              </view>
              <view style="display:table-cell;padding:6px 4px;border-bottom:1px solid #e0e0e0;text-align:center;color:#e6a23c;font-weight:500">
                <text>{{ item.allocated_quantity }}</text>
              </view>
              <view style="display:table-cell;padding:6px 4px;border-bottom:1px solid #e0e0e0;text-align:center;min-width:100px">
                <input type="number" :value="item.editQty" step="any" min="0" class="qty-input" @blur="onQtyBlur(item, $event)" @confirm="onQtyConfirm(item, $event)" :placeholder="item.item_unit" style="width:80px;padding:6px 8px;border:1px solid #dcdfe6;border-radius:4px;font-size:13px;text-align:center" />
              </view>
              <view style="display:table-cell;padding:6px 4px;border-bottom:1px solid #e0e0e0;text-align:center">
                <text :class="'tag ' + statusTag(item)" style="display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px">{{ itemStatusText(item) }}</text>
              </view>
              <view style="display:table-cell;padding:6px 4px;border-bottom:1px solid #e0e0e0;text-align:center;white-space:nowrap">
                <button class="btn btn-sm btn-primary" @click="submitItem(item)" :disabled="item.saving" style="padding:4px 10px;font-size:12px">
                  <text>{{ item.saving ? '...' : '保存' }}</text>
                </button>
                <text v-if="item.saved" style="color:#67c23a;font-weight:bold;margin-left:4px">✓</text>
                <text v-if="item.error" style="color:#f56c6c;font-weight:bold;margin-left:4px">!</text>
              </view>
            </view>
          </view>
        </view>
      </view>
      <!-- 保存提示 -->
      <view v-if="saveMsg" :class="'save-toast ' + (saveOk ? 'toast-ok' : 'toast-err')" style="position:fixed;bottom:20px;left:50%;transform:translateX(-50%);padding:10px 20px;border-radius:6px;font-size:14px;z-index:1000;box-shadow:0 4px 12px rgba(0,0,0,0.15)">
        <text>{{ saveMsg }}</text>
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
      batchName: "",
      saveMsg: "",
      saveOk: false
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
        var data = await apiGet('/employee/my-items?user_id=' + this.user.id + '&batch_id=' + batchId)
        var self = this
        this.myItems = data.map(function(item) {
          return {
            ...item,
            editQty: item.actual_quantity ?? item.allocated_quantity,
            saving: false, saved: false, error: ""
          }
        })
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
        var payload = {
          assignment_id: item.assignment_id,
          batch_item_id: item.item_id,
          user_id: this.user.id,
          actual_quantity: Number(item.editQty) || 0
        }
        var data = await apiPost('/employee/submit', payload)
        item.assignment_id = data.assignment_id || item.assignment_id
        item.saved = true
        item.actual_quantity = Number(item.editQty) || 0
        this.saveMsg = '已保存'
        this.saveOk = true
        var self = this
        setTimeout(function() { self.saveMsg = '' }, 2000)
        item._timeout = setTimeout(function() { item.saved = false }, 2000)
      } catch (e) {
        item.error = e.message || '网络错误'
        this.saveMsg = item.error
        this.saveOk = false
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
page { background: #f5f6fa; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; color: #333; }
view, text, input, button { box-sizing: border-box; }

.emp-page { max-width: 800px; margin: 0 auto; padding: 12px; font-size: 14px; }
.emp-header { display: flex; align-items: center; gap: 8px; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid #eee; flex-wrap: wrap; }
.emp-title { flex: 1; font-size: 18px; font-weight: 600; color: #303133; }
.emp-user-info { display: flex; align-items: center; gap: 8px; }
.emp-user { font-size: 13px; color: #606266; }

.empty-state { text-align: center; padding: 40px 20px; color: #909399; display: block; }
.empty-icon { font-size: 18px; margin-bottom: 8px; display: block; }

.batch-card { background: #fff; border-radius: 10px; padding: 14px 16px; margin-bottom: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); border: 1px solid #eee; }
.batch-card:active { transform: scale(0.98); background: #f5f7fa; }
.batch-card-name { font-size: 16px; font-weight: 600; color: #303133; margin-bottom: 6px; }
.batch-card-meta { display: flex; gap: 16px; font-size: 13px; color: #606266; }
.batch-card-date { font-size: 12px; color: #bbb; margin-top: 6px; display: block; }

.table-wrap { background: #fff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); overflow: hidden; }
.table-toolbar { padding: 12px 14px; border-bottom: 1px solid #eee; background: #fafafa; }
.table-info { font-size: 13px; color: #606266; }
.matrix-table-wrap { overflow-x: auto; }
.emp-table { }
.emp-table view[style*="display:table-row"]:nth-child(even) { background: #f8f9fc; }

.qty-input { -moz-appearance: textfield; }
.qty-input::-webkit-inner-spin-button,
.qty-input::-webkit-outer-spin-button { -webkit-appearance: none; margin: 0; }

.tag { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px; }
.tag-success { background: #f0f9eb; color: #67c23a; }
.tag-warning { background: #fdf6ec; color: #e6a23c; }
.tag-default { background: #f0f2f5; color: #909399; }

.save-toast { border: 1px solid; }
.toast-ok { background: #f0f9eb; color: #67c23a; border-color: #c2e7b0; }
.toast-err { background: #fef0f0; color: #f56c6c; border-color: #fbc4c4; }

.btn { display: inline-block; padding: 6px 14px; border: 1px solid #dcdfe6; border-radius: 4px; background: #fff; font-size: 13px; text-align: center; overflow: visible; line-height: 1.5; margin: 0; }
.btn:active { border-color: #409eff; color: #409eff; }
.btn-primary { background: #409eff; border-color: #409eff; color: #fff; }
.btn-primary:active { background: #66b1ff; border-color: #66b1ff; color: #fff; }
.btn-primary[disabled] { background: #a0cfff; border-color: #a0cfff; }
.btn-danger { background: #f56c6c; border-color: #f56c6c; color: #fff; }
.btn-danger:active { background: #f78989; border-color: #f78989; color: #fff; }
.btn-sm { padding: 4px 10px; font-size: 12px; line-height: 1.5; }
</style>
