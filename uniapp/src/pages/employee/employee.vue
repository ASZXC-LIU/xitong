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
      <view v-if="batchesLoading" class="empty-state">
        <text>正在加载任务…</text>
      </view>
      <view v-else-if="batchLoadError" class="empty-state">
        <text>{{ batchLoadError }}</text>
        <button class="btn btn-primary reload-button" @click="loadMyBatches">重新加载</button>
      </view>
      <view v-else-if="myBatches.length === 0" class="empty-state">
        <text class="empty-icon">暂无工单</text>
        <text>您还没有被分货货品</text>
      </view>
      <view v-for="b in displayBatches" :key="b.id" class="batch-card" @click="selectBatch(b)">
        <view class="batch-card-name">{{ b.name }}</view>
        <view class="batch-card-meta">
          <text>到货: {{ b.arrival_time }}</text>
          <text>货品: {{ b.item_count }} 种</text>
        </view>
        <text v-if="b.status === '已关闭'" class="batch-closed">该批次已关闭，仅可查看</text>
        <text class="batch-card-date">{{ b.created_at?.slice(0,10) }}</text>
      </view>
      <view v-if="loadingMore" class="history-status">正在加载更早任务…</view>
      <view v-else-if="historyLoadError" class="history-status">
        <text>{{ historyLoadError }}</text>
        <button class="btn btn-sm" @click="loadMoreBatches">重试</button>
      </view>
      <button v-else-if="hasMoreBatches" class="btn load-more-button" @click="loadMoreBatches">加载更早任务</button>
      <view v-else-if="myBatches.length" class="history-status">没有更早记录了</view>
    </view>

    <!-- 货品列表 -->
    <view v-if="selectedBatchId" class="task-wrap">
      <view class="table-toolbar">
        <text class="table-info">{{ batchName }} - 共 {{ myItems.length }} 种货品</text>
        <text v-if="isBatchClosed" class="batch-closed">该批次已关闭，仅可查看报货结果</text>
      </view>
      <view v-if="myItems.length === 0" class="empty-state">
        <text class="empty-icon">暂无货品</text>
      </view>
      <view v-else class="task-list">
        <view v-for="item in myItems" :key="item.item_id" class="product-card">
          <view class="product-card-header">
            <text class="product-name">{{ item.item_name }}</text>
            <text :class="'tag ' + statusTag(item)">{{ itemStatusText(item) }}</text>
          </view>
          <text class="allocation-text">分给您：{{ formatQuantity(item.allocated_quantity) }} {{ item.item_unit }}</text>

          <view v-if="isLocked(item)" class="locked-result">
            <text class="reported-text">已报货：{{ formatQuantity(item.actual_quantity) }} {{ item.item_unit }}</text>
            <text class="locked-text">已锁定</text>
          </view>

          <view v-else-if="isBatchClosed" class="locked-result">
            <text class="locked-text">批次已关闭，暂不能报货</text>
          </view>

          <view v-else class="report-form">
            <text class="field-label">实际报货数量（{{ item.item_unit }}）</text>
            <input
              type="number"
              :value="item.editQty"
              class="qty-input"
              placeholder="请输入数量"
              @input="onQtyInput(item, $event)"
            />
            <text class="field-help">没有货请填 0 后确认</text>
            <text v-if="item.error" class="field-error">{{ item.error }}</text>
            <button class="btn btn-primary submit-button" @click="submitItem(item)" :disabled="item.saving">
              <text>{{ item.saving ? '提交中' : '确认报货' }}</text>
            </button>
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
      batchesLoading: false,
      loadingMore: false,
      hasMoreBatches: false,
      historyCursor: null,
      batchLoadError: '',
      historyLoadError: '',
      myItems: [],
      selectedBatchId: null,
      batchName: "",
      selectedBatchStatus: "进行中",
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
  onReachBottom() {
    if (!this.selectedBatchId) this.loadMoreBatches()
  },
  computed: {
    displayBatches() {
      const pending = this.myBatches.filter(batch => !['已完成', '已关闭'].includes(batch.status))
      const history = this.myBatches.filter(batch => ['已完成', '已关闭'].includes(batch.status))
      return [...pending, ...history]
    }
  },
  methods: {
    statusTag(item) {
      if (this.isBatchClosed) return 'tag-default'
      if (this.isLocked(item)) return 'tag-success'
      if (item.allocated_quantity > 0) return 'tag-warning'
      return 'tag-default'
    },
    itemStatusText(item) {
      if (this.isBatchClosed) return '已关闭'
      if (this.isLocked(item)) return '已锁定'
      if (item.allocated_quantity > 0) return '待报货'
      return '未分配'
    },
    isLocked(item) {
      return item.report_status === '已锁定'
    },
    isBatchClosed() {
      return this.selectedBatchStatus === '已关闭'
    },
    formatQuantity(value) {
      return value == null ? '-' : value
    },
    async loadMyBatches() {
      this.batchesLoading = true
      this.batchLoadError = ''
      this.historyLoadError = ''
      try {
        const data = await apiGet('/employee/my-batches?window_days=15')
        this.myBatches = data.batches || []
        this.historyCursor = data.next_cursor || null
        this.hasMoreBatches = Boolean(this.historyCursor)
      } catch (e) {
        console.error('loadMyBatches', e)
        this.batchLoadError = e.message || '任务加载失败，请重试'
        this.myBatches = []
        this.historyCursor = null
        this.hasMoreBatches = false
      } finally {
        this.batchesLoading = false
      }
    },
    async loadMoreBatches() {
      if (this.loadingMore || !this.hasMoreBatches || !this.historyCursor) return
      this.loadingMore = true
      this.historyLoadError = ''
      try {
        const cursor = this.historyCursor
        const data = await apiGet(
          '/employee/my-batches?window_days=15&before_date=' + encodeURIComponent(cursor.before_date) + '&before_id=' + cursor.before_id
        )
        const knownIds = new Set(this.myBatches.map(batch => batch.id))
        const newBatches = (data.batches || []).filter(batch => !knownIds.has(batch.id))
        this.myBatches = [...this.myBatches, ...newBatches]
        this.historyCursor = data.next_cursor || null
        this.hasMoreBatches = Boolean(this.historyCursor)
      } catch (e) {
        console.error('loadMoreBatches', e)
        this.historyLoadError = e.message || '加载更早任务失败，请重试'
      } finally {
        this.loadingMore = false
      }
    },
    async selectBatchById(batchId) {
      try {
        var data = await apiGet('/employee/my-items?batch_id=' + batchId)
        this.myItems = data.map(function(item) {
          return {
            ...item,
            editQty: '',
            saving: false, saved: false, error: ""
          }
        })
        if (data.length && data[0].batch_status) this.selectedBatchStatus = data[0].batch_status
      } catch (e) {
        console.error('selectBatchById', e)
      }
    },
    selectBatch(b) {
      this.selectedBatchId = b.id
      this.batchName = b.name
      this.selectedBatchStatus = b.status || '进行中'
      this.selectBatchById(b.id)
    },
    backToBatches() {
      this.selectedBatchId = null
      this.myItems = []
      this.batchName = ""
      this.selectedBatchStatus = "进行中"
    },
    onQtyInput(item, event) {
      item.editQty = event.detail.value
      item.error = ''
    },
    reportQuantityError(item) {
      const value = String(item.editQty ?? '').trim()
      if (!value) return '请填写报货数量；没有货请填 0'
      if (!/^\d+(\.\d)?$/.test(value)) return '数量只能是最多一位小数的非负数字'
      if (Number(value) > Number(item.allocated_quantity)) return '报货数量不能大于分货数量'
      return ''
    },
    async submitItem(item) {
      if (item.saving || this.isLocked(item) || this.isBatchClosed) return
      const quantityError = this.reportQuantityError(item)
      if (quantityError) {
        item.error = quantityError
        return
      }
      if (item._timeout) clearTimeout(item._timeout)
      item.saving = true
      item.saved = false
      item.error = ""
      try {
        var payload = {
          assignment_id: item.assignment_id,
          actual_quantity: Number(item.editQty)
        }
        var data = await apiPost('/employee/submit', payload)
        item.assignment_id = data.assignment_id || item.assignment_id
        item.saved = true
        item.actual_quantity = Number(item.editQty)
        item.report_status = '已锁定'
        this.saveMsg = '报货已提交并锁定'
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

.emp-page { max-width: 800px; margin: 0 auto; padding: 12px; font-size: 16px; }
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
.batch-closed { display: block; margin-top: 8px; color: #667085; font-size: 14px; }
.history-status { padding: 16px; color: #667085; font-size: 14px; text-align: center; }
.load-more-button, .reload-button { display: block; width: 100%; min-height: 44px; margin-top: 12px; border-radius: 8px; }

.task-wrap { overflow: hidden; }
.table-toolbar { padding: 12px 14px; border-bottom: 1px solid #eee; background: #fafafa; }
.table-info { font-size: 14px; color: #606266; }
.task-list { display: flex; flex-direction: column; gap: 12px; margin-top: 12px; }
.product-card { background: #fff; border: 1px solid #d0d5dd; border-radius: 12px; padding: 16px; }
.product-card-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }
.product-name { flex: 1; font-size: 18px; font-weight: 700; line-height: 1.4; }
.allocation-text { display: block; margin-top: 10px; color: #667085; font-size: 16px; }
.report-form, .locked-result { margin-top: 16px; padding-top: 14px; border-top: 1px solid #eaecf0; }
.field-label { display: block; margin-bottom: 8px; font-weight: 600; }
.qty-input { width: 100%; min-height: 48px; padding: 10px 12px; border: 1px solid #98a2b3; border-radius: 8px; background: #fff; font-size: 20px; line-height: 1.4; }
.qty-input:focus { border-color: #07c160; outline: none; }
.field-help { display: block; margin-top: 8px; color: #667085; font-size: 14px; }
.field-error { display: block; margin-top: 8px; color: #c4320a; font-size: 14px; }
.submit-button { width: 100%; min-height: 48px; margin-top: 16px; border-color: #07c160; background: #07c160; border-radius: 8px; font-size: 17px; font-weight: 600; }
.submit-button[disabled] { border-color: #95d5a9; background: #95d5a9; }
.reported-text { display: block; color: #16803c; font-size: 18px; font-weight: 700; }
.locked-text { display: block; margin-top: 8px; color: #667085; font-size: 14px; }

.tag { display: inline-block; padding: 4px 8px; border-radius: 10px; font-size: 14px; white-space: nowrap; }
.tag-success { background: #ecfdf3; color: #16803c; }
.tag-warning { background: #fffaeb; color: #b54708; }
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
