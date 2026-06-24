<template>
  <view class="summary-page">
    <view class="page-header no-print">
      <text class="page-title">全品类汇总</text>
    </view>

    <view class="batch-select-bar no-print">
      <picker @change="onBatchChange" :value="summaryBatchIndex" :range="batchOptions" range-key="label" class="batch-picker">
        <view class="batch-select">{{ summaryBatchLabel || "-- 请选择批次 --" }}</view>
      </picker>
      <button class="btn btn-primary btn-sm" @click="doPrint" :disabled="!summaryData">打印</button>
      <button class="btn btn-sm btn-excel" @click="downloadExcel" :disabled="!summaryData">下载Excel</button>
    </view>

    <view v-if="!summaryData" class="empty-hint">
      <text>请选择一个批次查看汇总</text>
    </view>

    <scroll-view scroll-x v-else class="summary-scroll">
      <view class="summary-header-info">
        <text class="summary-batch-name">{{ summaryData.batch_name }}</text>
        <text class="summary-arrival" v-if="summaryData.arrival_time">到货时间: {{ summaryData.arrival_time }}</text>
      </view>
      <view class="summary-wrap" id="summary-table">
        <view class="s-row s-header">
          <text class="s-col-idx">序号</text>
          <text class="s-col-name">货品名称</text>
          <text class="s-col-unit">单位</text>
          <block v-for="emp in summaryEmployees" :key="emp.id">
            <text class="s-col-emp" style="min-width:70px">{{ emp.name }}</text>
          </block>
          <text class="s-col-total">总分货</text>
          <text class="s-col-total">总报货</text>
        </view>
        <view class="s-row s-sub-header">
          <text class="s-col-idx"></text>
          <text class="s-col-name"></text>
          <text class="s-col-unit"></text>
          <block v-for="emp in summaryEmployees" :key="emp.id">
            <text class="s-col-emp-sub" style="min-width:70px">
              <text class="sub-alloc">分货</text>
              <text class="sub-div">/</text>
              <text class="sub-actual">报货</text>
            </text>
          </block>
          <text class="s-col-total"></text>
          <text class="s-col-total"></text>
        </view>
        <view v-for="(d, idx) in summaryData.details" :key="d.item_name" class="s-row s-data">
          <text class="s-col-idx">{{ idx + 1 }}</text>
          <text class="s-col-name">{{ d.item_name }}</text>
          <text class="s-col-unit">{{ d.item_unit }}</text>
          <block v-for="emp in summaryEmployees" :key="emp.id">
            <view class="s-col-emp-cell" style="min-width:70px">
              <text class="cell-alloc">{{ getAlloc(d, emp.id) }}</text>
              <text class="cell-div">/</text>
              <text class="cell-actual">{{ getActual(d, emp.id) }}</text>
            </view>
          </block>
          <text class="s-col-total sum-alloc">{{ getAllocTotal(d) }}</text>
          <text class="s-col-total sum-actual">{{ d.total_actual ?? 0 }}</text>
        </view>
        <view v-if="summaryData.details &amp;&amp; summaryData.details.length &gt; 0" class="s-row s-total">
          <text class="s-col-idx"></text>
          <text class="s-col-name" style="font-weight:600;text-align:center">合计</text>
          <text class="s-col-unit"></text>
          <block v-for="emp in summaryEmployees" :key="emp.id">
            <view class="s-col-emp-cell" style="min-width:70px">
              <text class="cell-alloc total">{{ getColumnAllocTotal(emp.id) }}</text>
              <text class="cell-div">/</text>
              <text class="cell-actual total">{{ getColumnActualTotal(emp.id) }}</text>
            </view>
          </block>
          <text class="s-col-total sum-alloc">{{ getGrandAllocTotal() }}</text>
          <text class="s-col-total sum-actual">{{ getGrandActualTotal() }}</text>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script>
import { loadBatches, loadSummary, loadEmployees } from '../../utils/admin-api'
import { printSummaryTable } from '../../utils/print'

export default {
  data() {
    return { batches: [], employees: [], summaryData: null, summaryBatchIndex: -1 }
  },
  computed: {
    batchOptions() {
      return this.batches.map(b => ({ label: b.name + ' (' + (b.arrival_time || '') + ')', value: b.id }))
    },
    summaryEmployees() {
      if (!this.employees || !this.employees.length) return []
      return this.employees.map(e => ({ id: e.id, name: e.display_name || e.name }))
    },
    summaryBatchLabel() {
      if (this.summaryBatchIndex < 0 || this.summaryBatchIndex >= this.batchOptions.length) return ""
      return this.batchOptions[this.summaryBatchIndex].label
    }
  },
  async onShow() {
    await this.loadData()
  },
  methods: {
    async loadData() {
      try {
        this.employees = await loadEmployees()
        this.batches = await loadBatches()
        if (this.batches.length) {
          const sorted = [...this.batches].sort((a, b) => {
            const da = a.arrival_time || ''; const db = b.arrival_time || ''
            return db.localeCompare(da) || (b.id - a.id)
          })
          const latest = sorted[0]
          this.summaryBatchIndex = this.batches.findIndex(b => b.id === latest.id)
          this.summaryData = await loadSummary(latest.id)
        }
      } catch (e) { console.error('load summary error', e) }
    },
    async onBatchChange(e) {
      this.summaryBatchIndex = e.detail.value
      const batch = this.batches[this.summaryBatchIndex]
      if (!batch) return
      this.summaryData = null
      try { this.summaryData = await loadSummary(batch.id) } catch (e) { console.error(e) }
    },
    getAlloc(d, userId) {
      if (!d.assignments) return 0
      const a = d.assignments.find(a => a.user_id === userId)
      return a ? (a.allocated_quantity ?? 0) : 0
    },
    getActual(d, userId) {
      if (!d.assignments) return '-'
      const a = d.assignments.find(a => a.user_id === userId)
      return a && a.actual_quantity != null ? a.actual_quantity : '-'
    },
    getAllocTotal(d) {
      if (!d.assignments) return 0
      return d.assignments.reduce((s, a) => s + (a.allocated_quantity ?? 0), 0)
    },
    getColumnAllocTotal(userId) {
      if (!this.summaryData || !this.summaryData.details) return 0
      return this.summaryData.details.reduce((s, d) => s + Number(this.getAlloc(d, userId)), 0)
    },
    getColumnActualTotal(userId) {
      if (!this.summaryData || !this.summaryData.details) return 0
      return this.summaryData.details.reduce((s, d) => {
        const v = this.getActual(d, userId); return s + (v === '-' ? 0 : Number(v))
      }, 0)
    },
    getGrandAllocTotal() {
      if (!this.summaryData || !this.summaryData.details) return 0
      return this.summaryData.details.reduce((s, d) => s + this.getAllocTotal(d), 0)
    },
    getGrandActualTotal() {
      if (!this.summaryData || !this.summaryData.details) return 0
      return this.summaryData.details.reduce((s, d) => s + (d.total_actual ?? 0), 0)
    },
    doPrint() {
      printSummaryTable(this.summaryData)
    },
    // #ifdef H5
    downloadExcel() {
      if (!this.summaryData) return
      var h = '<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">'
      h += '<head><meta charset="UTF-8"><style>th,td{border:1px solid #000;padding:4px 6px;font-size:12px;text-align:center}th{background:#d9e1f2;font-weight:700}td{vertical-align:middle}</style></head><body>'
      h += '<h2 style="text-align:center">' + (this.summaryData.batch_name || '全品类汇总') + '</h2>'
      h += '<p style="text-align:center">到货时间: ' + (this.summaryData.arrival_time || '') + '</p>'
      h += '<table><thead><tr><th>序号</th><th>货品名称</th><th>单位</th>'
      for (var i = 0; i < this.summaryEmployees.length; i++) { h += '<th colspan="2">' + this.summaryEmployees[i].name + '</th>' }
      h += '<th>总分货</th><th>总报货</th></tr></thead><tbody>'
      for (var i = 0; i < this.summaryData.details.length; i++) {
        var d = this.summaryData.details[i]
        h += '<tr><td>' + (i+1) + '</td><td style="text-align:left">' + d.item_name + '</td><td>' + (d.item_unit||'') + '</td>'
        for (var j = 0; j < this.summaryEmployees.length; j++) {
          var emp = this.summaryEmployees[j]
          h += '<td>' + this.getAlloc(d,emp.id) + '</td><td>' + this.getActual(d,emp.id) + '</td>'
        }
        h += '<td>' + this.getAllocTotal(d) + '</td><td>' + (d.total_actual||0) + '</td></tr>'
      }
      h += '<tr style="font-weight:600;background:#eef1f8"><td></td><td style="text-align:center">合计</td><td></td>'
      for (var j = 0; j < this.summaryEmployees.length; j++) {
        var emp = this.summaryEmployees[j]
        h += '<td>' + this.getColumnAllocTotal(emp.id) + '</td><td>' + this.getColumnActualTotal(emp.id) + '</td>'
      }
      h += '<td>' + this.getGrandAllocTotal() + '</td><td>' + this.getGrandActualTotal() + '</td></tr>'
      h += '</tbody></table></body></html>'
      var blob = new Blob([h], {type: 'application/vnd.ms-excel'})
      var url = URL.createObjectURL(blob)
      var a = document.createElement('a')
      a.href = url; a.download = (this.summaryData.batch_name || '全品类汇总') + '.xls'
      document.body.appendChild(a); a.click(); document.body.removeChild(a)
      URL.revokeObjectURL(url)
    }
    // #endif
    // #ifdef MP-WEIXIN
    downloadExcel() {
      uni.showToast({ title: "小程序暂不支持下载Excel", icon: "none" })
    }
    // #endif
  }
}
</script>

<style>
.summary-page { padding: 12px; }
.page-header { margin-bottom: 4px; }
.page-title { font-size: 18px; font-weight: 600; color: #303133; }
.batch-select-bar { display: flex; align-items: center; gap: 8px; background: #fff; border-radius: 8px; padding: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 12px; flex-wrap: wrap; }
.batch-picker { flex: 1; min-width: 200px; }
.batch-select { border: 1px solid #dcdfe6; border-radius: 4px; padding: 8px 12px; font-size: 14px; background: #fff; }
.btn-excel { background: #67c23a; border-color: #67c23a; color: #fff; }
.summary-scroll { overflow-x: auto; background: #fff; border-radius: 8px; padding: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.summary-header-info { display: flex; gap: 16px; align-items: baseline; margin-bottom: 10px; }
.summary-batch-name { font-size: 15px; font-weight: 600; color: #303133; }
.summary-arrival { font-size: 12px; color: #909399; }
.summary-wrap { min-width: 500px; border: 1px solid #000; }
.s-row { display: flex; border-bottom: 1px solid #000; }
.s-row.s-header { background: #d9e1f2; font-weight: 700; font-size: 12px; color: #333; }
.s-row.s-sub-header { background: #ecf5ff; font-size: 10px; color: #99c9ff; }
.s-row.s-data:nth-child(even) { background: #f8f9fc; }
.s-row.s-total { background: #eef1f8; font-weight: 600; border-top: 2px solid #000; }
.s-row text, .s-row view { padding: 3px 2px; border-right: 1px solid #000; text-align: center; font-size: 12px; white-space: nowrap; vertical-align: middle; }
.s-col-idx { min-width: 32px; width: 32px; }
.s-col-name { min-width: 70px; text-align: left !important; padding-left: 6px !important; font-weight: 500; }
.s-col-unit { min-width: 35px; width: 35px; font-size: 11px; color: #606266; }
.s-col-emp { min-width: 70px; background: #ecf5ff; padding: 4px 2px !important; }
.s-col-emp-sub { min-width: 70px; background: #ecf5ff; padding: 2px 2px !important; }
.s-col-total { min-width: 38px; background: #fdf6ec; font-weight: 600; color: #e6a23c; }
.s-col-emp-cell { display: flex; justify-content: center; gap: 2px; padding: 3px 2px; min-width: 70px; border-right: 1px solid #000; }
.sub-alloc { color: #e6a23c; }
.sub-actual { color: #67c23a; }
.sub-div { color: #ccc; }
.cell-alloc { color: #e6a23c; font-weight: 500; }
.cell-actual { color: #67c23a; font-weight: 500; }
.cell-div { color: #ccc; font-size: 10px; }
.cell-alloc.total, .cell-actual.total { font-weight: 600; }
.sum-alloc { color: #e6a23c; }
.sum-actual { color: #67c23a; }
.empty-hint { text-align: center; color: #909399; font-size: 15px; padding: 60px 20px; }
@media print { .no-print { display: none !important; } }
.btn { display: inline-block; padding: 6px 14px; border: 1px solid #dcdfe6; border-radius: 4px; background: #fff; font-size: 13px; }
.btn-primary { background: #409eff; border-color: #409eff; color: #fff; }
.btn-sm { padding: 4px 10px; font-size: 12px; }
</style>
