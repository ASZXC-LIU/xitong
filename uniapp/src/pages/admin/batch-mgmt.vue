<template>
  <view class="batch-page">
    <!-- 批次选择栏 -->
    <view class="batch-select-bar">
      <picker @change="onBatchChange" :value="selectedBatchIndex" :range="batchOptions" range-key="label" class="batch-picker">
        <view class="batch-select">{{ selectedBatchLabel || "-- 请选择批次 --" }}</view>
      </picker>
      <button class="btn btn-sm btn-primary" @click="showBatchForm = true">+ 新建</button>
      <button class="btn btn-sm" @click="goToSummary" :disabled="!selectedBatchId">明细</button>
      <button class="btn btn-sm btn-danger" @click="doDeleteBatch" :disabled="!selectedBatchId">删除</button>
    </view>

    <!-- 货品矩阵表格 -->
    <scroll-view scroll-x class="matrix-scroll" v-if="selectedBatchId">
      <view class="table-header-bar">
        <text class="table-title">货品列表</text>
        <button class="btn btn-sm btn-primary" @click="showItemForm = true">+ 添加货品</button>
      </view>

      <view v-if="items.length === 0" class="empty-hint">暂无货品</view>

      <view v-else class="matrix-wrap">
        <!-- 表头 -->
        <view class="matrix-row header">
          <text class="cell-name">货品名称</text>
          <text class="cell-unit">单位</text>
          <block v-for="emp in matrixEmployees" :key="emp.id">
            <text class="cell-emp-header" style="text-align:center">{{ emp.name }}</text>
            <text class="cell-emp-header sub">{{ emp.name }}</text>
          </block>
          <text class="cell-total-h col-type-alloc">总分货</text>
          <text class="cell-total-h col-type-actual">总报货</text>
          <text class="cell-status-h">状态</text>
          <text class="cell-remark-h">备注</text>
          <text class="cell-action-h">操作</text>
        </view>
        <!-- 子表头 -->
        <view class="matrix-row sub-header">
          <text class="cell-name"></text>
          <text class="cell-unit"></text>
          <block v-for="emp in matrixEmployees" :key="emp.id">
            <text class="cell-emp-sub col-type-alloc" style="color:#99c9ff;font-size:10px;text-align:center">分货</text>
            <text class="cell-emp-sub col-type-actual" style="color:#99c9ff;font-size:10px;text-align:center">报货</text>
          </block>
          <text class="cell-total-h"></text>
          <text class="cell-total-h"></text>
          <text class="cell-status-h"></text>
          <text class="cell-remark-h"></text>
          <text class="cell-action-h"></text>
        </view>

        <!-- 数据行 -->
        <view v-for="item in items" :key="item.id" class="matrix-row data-row">
          <text class="cell-name" @click="showDetail(item)">{{ item.name }}</text>
          <text class="cell-unit">{{ item.unit }}</text>
          <block v-for="emp in matrixEmployees" :key="emp.id">
            <view class="cell-qty-alloc col-type-alloc" @mouseenter="onCellEnter($event, item, emp, 0)" @mouseleave="onCellLeave">
              <input type="number" :value="getItemQty(item, emp.id)" @blur="saveEdit(item, emp.id, $event.detail.value)" step="any" min="0" class="qty-input" />
            </view>
            <view class="cell-qty-actual col-type-actual" @mouseenter="onCellEnter($event, item, emp, 1)" @mouseleave="onCellLeave">
              <text class="actual-qty">{{ getItemActual(item, emp.id) }}</text>
            </view>
          </block>
          <text class="cell-total-v col-type-alloc" @mouseenter="onCellEnter($event, item, null, 2)" @mouseleave="onCellLeave">{{ getItemTotal(item) }}</text>
          <text class="cell-total-v actual col-type-actual" @mouseenter="onCellEnter($event, item, null, 3)" @mouseleave="onCellLeave">{{ getItemActualTotal(item) }}</text>
          <view class="cell-status-v">
            <text :class="'badge ' + (item.status==='未分配' ? 'badge-pending' : item.status==='未报货' ? 'badge-warn' : 'badge-ok')">{{ item.status }}</text>
          </view>
          <text class="cell-remark-v">{{ item.remark || "无备注" }}</text>
          <view class="cell-action-v"><button class="btn btn-xs btn-danger" @click="doDeleteItem(item.id)">删除</button></view>
        </view>

        <!-- 合计行 -->
        <view v-if="items.length > 1" class="matrix-row total-row">
          <text class="cell-name" style="font-weight:600">合计</text>
          <text class="cell-unit"></text>
          <block v-for="emp in matrixEmployees" :key="emp.id">
            <text class="cell-total-v">{{ getColumnTotal(emp.id) }}</text>
            <text class="cell-total-v actual">{{ getMatrixColumnActualTotal(emp.id) }}</text>
          </block>
          <text class="cell-total-v">{{ getGrandTotal() }}</text>
          <text class="cell-total-v actual">{{ getMatrixGrandActualTotal() }}</text>
          <view class="cell-status-v"></view>
          <text class="cell-remark-v"></text>
          <view class="cell-action-v"></view>
        </view>
      </view>
    </scroll-view>
    <view v-else-if="!selectedBatchId" class="empty-hint" style="margin-top:60px">请选择一个批次</view>

    <!-- 批次表单弹窗 -->
    <uni-popup v-if="showBatchForm" class="modal-mask" @click="showBatchForm=false">
      <view class="modal-card" @click.stop>
        <text class="modal-title">{{ editingBatchId ? "编辑批次" : "新建报货批次" }}</text>
        <input v-model="batchForm.name" placeholder="批次名称" class="uni-input" />
        <input v-model="batchForm.arrival_time" placeholder="到货时间 (YYYY-MM-DD)" class="uni-input" />
        <input v-model="batchForm.batch_remark" placeholder="备注" class="uni-input" />
        <view class="modal-actions">
          <button class="btn" @click="showBatchForm=false">取消</button>
          <button class="btn btn-primary" @click="saveBatch">{{ editingBatchId ? "保存" : "创建" }}</button>
        </view>
        <text v-if="batchMsg" :style="{color: batchMsgOk ? '#67c23a' : '#f56c6c'}">{{ batchMsg }}</text>
      </view>
    </uni-popup>

    <!-- 货品表单弹窗 -->
    <uni-popup v-if="showItemForm" class="modal-mask" @click="showItemForm=false">
      <view class="modal-card" @click.stop>
        <text class="modal-title">添加货品</text>
        <input v-model="itemForm.name" placeholder="货品名称" class="uni-input" />
        <input v-model="itemForm.unit" placeholder="单位" class="uni-input" />
        <input v-model="itemForm.spec" placeholder="规格" class="uni-input" />
        <input v-model="itemForm.remark" placeholder="备注" class="uni-input" />
        <view class="modal-actions">
          <button class="btn" @click="showItemForm=false">取消</button>
          <button class="btn btn-primary" @click="addNewItem">添加</button>
        </view>
        <text v-if="itemMsg" style="color:#67c23a">{{ itemMsg }}</text>
      </view>
    </uni-popup>


<!-- Tooltip -->
<view class="matrix-tooltip" v-if="tooltip.visible" :style="{left:tooltip.x+'px',top:tooltip.y+'px'}">{{tooltip.text}}</view>

    <!-- 货品详情弹窗 (手机端) -->
    <uni-popup v-if="detailItem" class="modal-mask" @click="detailItem=null">
      <view class="modal-card modal-card-wide" @click.stop>
        <view class="modal-header">
          <text class="modal-title">{{ detailItem.name }}</text>
          <button class="btn btn-sm" @click="detailItem=null">关闭</button>
        </view>
        <view class="detail-info">
          <text>单位: {{ detailItem.unit }}</text>
          <text v-if="detailItem.spec">规格: {{ detailItem.spec }}</text>
          <text>备注: {{ detailItem.remark || "无" }}</text>
          <text :class="'badge ' + (detailItem.status==='未分配' ? 'badge-pending' : detailItem.status==='未报货' ? 'badge-warn' : 'badge-ok')">{{ detailItem.status }}</text>
        </view>
        <view class="assign-list">
          <view class="assign-header">
            <text style="flex:1">员工</text>
            <text style="width:80px;text-align:center">分货数量</text>
            <text style="width:80px;text-align:center">已报数量</text>
          </view>
          <view v-for="emp in employees" :key="emp.id" class="assign-row">
            <text style="flex:1;font-weight:500">{{ emp.display_name || emp.name }}</text>
            <view style="width:80px;text-align:center">
              <input type="number" :value="getItemQty(detailItem, emp.id)" @blur="saveEdit(detailItem, emp.id, $event.detail.value)" step="any" min="0" class="qty-input" />
            </view>
            <text style="width:80px;text-align:center;color:#67c23a;font-weight:500">{{ getItemActual(detailItem, emp.id) }}</text>
          </view>
        </view>
        <view class="assign-total">
          <text>合计</text>
          <view style="display:flex;gap:24px">
            <text style="color:#e6a23c">分货: {{ getItemTotal(detailItem) }}</text>
            <text style="color:#67c23a">报货: {{ getItemActualTotal(detailItem) }}</text>
          </view>
        </view>
      </view>
    </uni-popup>
  </view>
</template>

<script>
import { loadBatches, loadItems, loadEmployees, loadCargoTypes, createBatch, updateBatch, deleteBatch, addItem, deleteItem as apiDeleteItem, saveAssignments, loadSummary } from "../../utils/admin-api"
import { getStorage } from "../../utils/storage"

export default {
  data() {
    return {
      batches: [], employees: [], items: [],
      selectedBatchId: null,
      // 批次表单
      showBatchForm: false, editingBatchId: null,
      batchForm: { name: "", arrival_time: "", batch_remark: "", batch_date: "" },
      batchMsg: "", batchMsgOk: false,
      // 货品表单
      showItemForm: false,
      itemForm: { name: "", unit: "", spec: "", remark: "" },
      itemMsg: "",
      // 详情
      detailItem: null,
      hoverRow: -1,
      hoverCol: -1,
      tooltip: { visible: false, x: 0, y: 0, text: "" },
      hoverRow: -1,
      hoverCol: -1,
      tooltip: { visible: false, x: 0, y: 0, text: "" }
    }
  },
  computed: {
    sortedBatches() {
      return [...this.batches].sort((a, b) => {
        const da = a.arrival_time || ""; const db = b.arrival_time || ""
        return db.localeCompare(da) || (b.id - a.id)
      })
    },
    selectedBatchIndex() {
      return this.sortedBatches.findIndex(b => b.id === this.selectedBatchId)
    },
    selectedBatchLabel() {
      const b = this.sortedBatches.find(b => b.id === this.selectedBatchId)
      return b ? (b.name + " (" + b.arrival_time + " | " + (b.item_count || 0) + " 个货)") : ""
    },
    batchOptions() {
      return this.sortedBatches.map(b => ({
        label: b.name + " (" + (b.arrival_time || "") + " | " + (b.item_count || 0) + " 个货)",
        value: b.id
      }))
    },
    matrixEmployees() {
      return this.employees.map(e => ({ id: e.id, name: e.display_name || e.name }))
    }
  },
  async onShow() {
    await Promise.all([this.loadBatches(), this.loadEmployees()])
    // 自动选择最新批次
    if (!this.selectedBatchId && this.sortedBatches.length) {
      await this.selectBatch(this.sortedBatches[0])
    }
  },
  methods: {
    async loadBatches() {
      try { this.batches = await loadBatches() } catch (e) { console.error(e) }
    },
    async loadEmployees() {
      try { this.employees = await loadEmployees() } catch (e) { console.error(e) }
    },
    async loadItems(batchId) {
      try {
        this.items = await loadItems(batchId)
        this.items.forEach(item => { if (!item.assignments) item.assignments = [] })
      } catch (e) { console.error(e) }
    },
    async selectBatch(b) {
      this.selectedBatchId = b.id
      await this.loadItems(b.id)
    },
    async onBatchChange(e) {
      const idx = parseInt(e.detail.value)
      if (idx >= 0 && idx < this.sortedBatches.length) {
        await this.selectBatch(this.sortedBatches[idx])
      }
    },
    goToSummary() {
      if (this.selectedBatchId) {
        uni.navigateTo({ url: "/pages/admin/summary?batchId=" + this.selectedBatchId })
      }
    },
    // 批次 CRUD
    async saveBatch() {
      if (!this.batchForm.name) return
      try {
        if (this.editingBatchId) {
          await updateBatch(this.editingBatchId, this.batchForm)
          this.batchMsg = "更新成功"
        } else {
          await createBatch(this.batchForm)
          this.batchMsg = "创建成功"
        }
        this.batchMsgOk = true
        await this.loadBatches()
        setTimeout(() => { this.showBatchForm = false; this.batchMsg = "" }, 1000)
      } catch (e) {
        this.batchMsg = e.response?.data?.error || "操作失败"
        this.batchMsgOk = false
      }
    },
    async doDeleteBatch() {
      if (!this.selectedBatchId) return
      if (!confirm("确认删除此批次?")) return
      try {
        await deleteBatch(this.selectedBatchId)
        this.selectedBatchId = null
        this.items = []
        await this.loadBatches()
      } catch (e) { console.error(e) }
    },
    // 货品 CRUD
    async addNewItem() {
      if (!this.itemForm.name || !this.selectedBatchId) return
      try {
        await addItem(this.selectedBatchId, this.itemForm)
        this.itemMsg = "添加成功"
        this.itemForm = { name: "", unit: "", spec: "", remark: "" }
        await this.loadItems(this.selectedBatchId)
        await this.loadBatches()
        setTimeout(() => { this.showItemForm = false; this.itemMsg = "" }, 1000)
      } catch (e) { console.error(e) }
    },
    async doDeleteItem(id) {
      if (!confirm("确认删除?")) return
      try {
        await apiDeleteItem(id)
        await this.loadItems(this.selectedBatchId)
      } catch (e) { console.error(e) }
    },
    // 分货编辑
    async saveEdit(item, userId, newValue) {
      const newQty = Number(newValue) || 0
      const existing = item.assignments || []
      let assignments = existing.map(a => ({
        user_id: a.user_id,
        allocated_quantity: a.user_id === userId ? newQty : (a.allocated_quantity || 0)
      }))
      if (!existing.find(a => a.user_id === userId)) {
        assignments.push({ user_id: userId, allocated_quantity: newQty })
      }
      try {
        await saveAssignments(item.id, assignments)
        await this.loadItems(this.selectedBatchId)
      } catch (e) { console.error(e) }
    },
    // 数值辅助
    getItemQty(item, userId) {
      if (!item.assignments) return 0
      const a = item.assignments.find(a => a.user_id === userId)
      return a ? (a.allocated_quantity || 0) : 0
    },
    getItemActual(item, userId) {
      if (!item.assignments) return 0
      const a = item.assignments.find(a => a.user_id === userId)
      return a && a.actual_quantity != null ? a.actual_quantity : 0
    },
    getItemTotal(item) {
      if (!item.assignments) return 0
      return item.assignments.reduce((s, a) => s + (a.allocated_quantity || 0), 0)
    },
    getItemActualTotal(item) {
      if (!item.assignments) return 0
      return item.assignments.reduce((s, a) => s + (a.actual_quantity || 0), 0)
    },
    getColumnTotal(userId) {
      let total = 0
      for (const item of this.items) {
        const a = item.assignments?.find(a => a.user_id === userId)
        if (a) total += (a.allocated_quantity || 0)
      }
      return total
    },
    getMatrixColumnActualTotal(userId) {
      let total = 0
      for (const item of this.items) {
        const a = item.assignments?.find(a => a.user_id === userId)
        if (a) total += (a.actual_quantity || 0)
      }
      return total
    },
    getGrandTotal() {
      return this.items.reduce((s, item) => {
        if (item.assignments) item.assignments.forEach(a => s += (a.allocated_quantity || 0))
        return s
      }, 0)
    },
    getMatrixGrandActualTotal() {
      return this.items.reduce((s, item) => {
        if (item.assignments) item.assignments.forEach(a => s += (a.actual_quantity || 0))
        return s
      }, 0)
    },
    showDetail(item) {
      this.detailItem = item
    },
    // Hover & Tooltip
    onCellEnter(event, item, emp, colType) {
      var text = ''
      if (item && item.name) {
        var itemName = item.name
        var empName = emp && emp.name ? emp.name : ''
        if (colType === 0 && empName) text = itemName + ' ' + empName + ' 分货：' + this.getItemQty(item, emp.id)
        else if (colType === 1 && empName) text = itemName + ' ' + empName + ' 报货：' + this.getItemActual(item, emp.id)
        else if (colType === 2) text = itemName + '总分货：' + this.getItemTotal(item)
        else if (colType === 3) text = itemName + '总报货：' + this.getItemActualTotal(item)
      }
      if (text) { this.tooltip.text = text; this.tooltip.x = event.clientX + 12; this.tooltip.y = event.clientY - 10; this.tooltip.visible = true }
    },
    onCellLeave() {
      this.hoverRow = -1
      this.hoverCol = -1
      this.tooltip.visible = false
    }
  }
}
</script>

<style>
.batch-page { padding: 12px; }
.batch-select-bar { display: flex; align-items: center; gap: 6px; background: #fff; border-radius: 8px; padding: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 12px; flex-wrap: wrap; }
.batch-picker { flex: 1; min-width: 200px; }
.batch-select { border: 1px solid #dcdfe6; border-radius: 4px; padding: 8px 12px; font-size: 14px; background: #fff; }
.matrix-scroll { overflow-x: auto; background: #fff; border-radius: 8px; padding: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.table-header-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.table-title { font-weight: 600; font-size: 14px; }
.matrix-wrap { min-width: 600px; border: 1px solid #000; }
.matrix-row { display: flex; border-bottom: 1px solid #000; }
.matrix-row.header { background: #d9e1f2; font-weight: 700; font-size: 12px; color: #333; }
.matrix-row.sub-header { background: #ecf5ff; font-size: 10px; }
.matrix-row.data-row:nth-child(even) { background: #f8f9fc; }
.matrix-row.total-row { background: #eef1f8; font-weight: 600; border-top: 2px solid #000; }
.matrix-row text, .matrix-row view { padding: 3px 2px; border-right: 1px solid #000; text-align: center; font-size: 12px; white-space: nowrap; }
.cell-name { min-width: 80px; text-align: left !important; padding-left: 6px !important; }
.cell-unit { min-width: 35px; }
.cell-emp-header { min-width: 40px; background: #ecf5ff; color: #409eff; }
.cell-total-h, .cell-total-v { min-width: 38px; background: #fdf6ec; color: #e6a23c; font-weight: 600; }
.cell-total-v.actual { color: #67c23a; }
.cell-status-h, .cell-status-v { min-width: 40px; }
.cell-remark-h, .cell-remark-v { min-width: 50px; font-size: 11px; }
.cell-action-h, .cell-action-v { min-width: 50px; }
.qty-input { width: 36px; padding: 2px 1px; border: 1px solid #dcdfe6; border-radius: 2px; font-size: 12px; text-align: center; }
.actual-qty { font-size: 11px; color: #67c23a; font-weight: 600; }
.actual-qty::before { content: "报"; font-size: 9px; color: #999; margin-right: 1px; }
.badge { display: inline-block; padding: 2px 6px; border-radius: 10px; font-size: 10px; }
.badge-pending { background: #fdf6ec; color: #e6a23c; }
.badge-warn { background: #fef0f0; color: #f56c6c; }
.badge-ok { background: #f0f9eb; color: #67c23a; }
.empty-hint { text-align: center; color: #909399; font-size: 14px; padding: 20px; }

/* 弹窗 */
.modal-mask { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal-card { background: #fff; border-radius: 10px; padding: 24px; width: 480px; max-width: 90vw; max-height: 80vh; }
.modal-card-wide { width: 640px; }
.modal-title { display: block; font-size: 18px; font-weight: 600; margin-bottom: 16px; }
.modal-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 16px; }
.uni-input { width: 100%; padding: 8px 10px; border: 1px solid #dcdfe6; border-radius: 4px; font-size: 14px; margin-bottom: 12px; }

/* 详情弹窗 */
.modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.detail-info { display: flex; gap: 16px; flex-wrap: wrap; font-size: 13px; color: #909399; margin-bottom: 16px; align-items: center; }
.assign-list { border-top: 1px solid #eee; }
.assign-header { display: flex; font-weight: 600; font-size: 13px; color: #666; padding: 8px 0; border-bottom: 1px solid #eee; }
.assign-row { display: flex; align-items: center; padding: 10px 0; border-bottom: 1px solid #f0f0f0; }
.assign-total { margin-top: 12px; padding-top: 12px; border-top: 2px solid #409eff; display: flex; justify-content: space-between; font-weight: 600; font-size: 14px; }

/* 通用按钮 */
.btn { display: inline-block; padding: 6px 14px; border: 1px solid #dcdfe6; border-radius: 4px; background: #fff; font-size: 13px; }
.btn-primary { background: #409eff; border-color: #409eff; color: #fff; }
.btn-danger { background: #f56c6c; border-color: #f56c6c; color: #fff; }
.btn-sm { padding: 4px 10px; font-size: 12px; }
.btn-xs { padding: 2px 8px; font-size: 11px; }

/* Column type colors */
.col-type-alloc { background-color: #fff8e1 !important; }
.col-type-actual { background-color: #e8f5e9 !important; }
.col-type-alloc.cell-total-h, .col-type-alloc.cell-total-v { background-color: #fff8e1 !important; }
.col-type-actual.cell-total-h, .col-type-actual.cell-total-v { background-color: #e8f5e9 !important; }
/* Hover row highlight */
.matrix-row.data-row.hover-row { background-color: #dde4f0 !important; }
.matrix-row.data-row.hover-row .col-type-alloc { background-color: #ffe8b0 !important; }
.matrix-row.data-row.hover-row .col-type-actual { background-color: #c8e6c9 !important; }
.matrix-row.data-row .hover-col { background-color: #d0d8e8 !important; }
.matrix-row.data-row .col-type-alloc.hover-col { background-color: #ffd699 !important; }
.matrix-row.data-row .col-type-actual.hover-col { background-color: #a5d6a7 !important; }
/* Tooltip */
.matrix-tooltip { position: fixed; z-index: 10000; background: rgba(51,51,51,0.92); color: #fff; padding: 6px 10px; border-radius: 4px; font-size: 12px; pointer-events: none; white-space: nowrap; max-width: 280px; line-height: 1.5; }

</style>