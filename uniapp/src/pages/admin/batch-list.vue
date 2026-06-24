<template>
  <view class="batch-list-page">
    <view class="page-header">
      <text class="page-title">分单批次</text>
      <button class="btn btn-sm btn-primary" @click="showForm = true">+ 新建</button>
    </view>

    <view v-if="batches.length === 0" class="empty-hint">暂无数据</view>

    <view v-for="b in sortedBatches" :key="b.id" class="batch-item">
      <view class="batch-item-row">
        <text class="batch-item-name">{{ b.name }}</text>
        <text class="batch-item-arrival">到货: {{ b.arrival_time }}</text>
      </view>
      <view class="batch-item-row sub">
        <text>货品数: {{ b.item_count }}</text>
        <text class="batch-item-remark">{{ b.batch_remark || "" }}</text>
        <text class="batch-item-date">{{ b.created_at?.slice(0,10) }}</text>
      </view>
      <view class="batch-item-actions">
        <button class="btn btn-xs" @click="editBatch(b)">编辑</button>
        <button class="btn btn-xs btn-danger" @click="doDelete(b)">删除</button>
      </view>
    </view>

    <!-- Form modal -->
    <view v-if="showForm" class="modal-mask" @click="showForm=false">
      <view class="modal-card" @click.stop>
        <text class="modal-title">{{ editId ? "编辑批次" : "新建批次" }}</text>
        <input class="uni-input" v-model="form.name" placeholder="批次名称" />
        <input class="uni-input" v-model="form.arrival_time" placeholder="到货时间" />
        <input class="uni-input" v-model="form.batch_remark" placeholder="备注" />
        <view class="modal-actions">
          <button class="btn" @click="showForm=false">取消</button>
          <button class="btn btn-primary" @click="saveBatch">保存</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { loadBatches, createBatch, updateBatch, deleteBatch } from "../../utils/admin-api"
export default {
  data() {
    return { batches: [], showForm: false, form: { name: "", arrival_time: "", batch_remark: "" }, editId: null }
  },
  computed: {
    sortedBatches() {
      return [...this.batches].sort((a, b) => (b.arrival_time||"").localeCompare(a.arrival_time||"") || (b.id - a.id))
    }
  },
  async onShow() { await this.loadData() },
  methods: {
    async loadData() {
      try { this.batches = await loadBatches() } catch (e) { console.error(e) }
    },
    editBatch(b) {
      this.editId = b.id; this.form = { name: b.name, arrival_time: b.arrival_time, batch_remark: b.batch_remark || "" }; this.showForm = true
    },
    async saveBatch() {
      try {
        if (this.editId) { await updateBatch(this.editId, this.form) } else { await createBatch(this.form) }
        this.showForm = false; this.editId = null; this.form = { name: "", arrival_time: "", batch_remark: "" }; await this.loadData()
      } catch (e) { console.error(e) }
    },
    async doDelete(b) {
      try { await deleteBatch(b.id); await this.loadData() } catch (e) { console.error(e) }
    }
  }
}
</script>

<style>
.batch-list-page { padding: 12px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.page-title { font-size: 18px; font-weight: 600; }
.batch-item { background: #fff; border-radius: 8px; padding: 14px; margin-bottom: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.batch-item-row { display: flex; align-items: center; gap: 12px; margin-bottom: 4px; }
.batch-item-row.sub { font-size: 12px; color: #909399; }
.batch-item-name { font-size: 16px; font-weight: 600; flex: 1; }
.batch-item-arrival { font-size: 13px; color: #606266; }
.batch-item-remark { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.batch-item-date { color: #bbb; }
.batch-item-actions { margin-top: 8px; padding-top: 8px; border-top: 1px solid #f0f0f0; display: flex; gap: 8px; }
.empty-hint { text-align: center; color: #909399; padding: 40px; }
.modal-mask { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal-card { background: #fff; border-radius: 10px; padding: 24px; width: 480px; max-width: 90vw; }
.modal-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; display: block; }
.modal-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 16px; }
.uni-input { width: 100%; padding: 8px 10px; border: 1px solid #dcdfe6; border-radius: 4px; font-size: 14px; margin-bottom: 12px; box-sizing: border-box; }
.btn { display: inline-block; padding: 6px 14px; border: 1px solid #dcdfe6; border-radius: 4px; background: #fff; font-size: 13px; }
.btn-primary { background: #409eff; border-color: #409eff; color: #fff; }
.btn-sm { padding: 4px 10px; font-size: 12px; }
.btn-xs { padding: 2px 8px; font-size: 11px; }
.btn-danger { background: #f56c6c; border-color: #f56c6c; color: #fff; }
</style>
