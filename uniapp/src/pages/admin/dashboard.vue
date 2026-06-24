<template>
  <view class="dashboard-page">
    <!-- 顶部导航栏 -->
    <view class="nav-header">
      <text class="nav-title">分单系统</text>
      <view class="nav-menu">
        <text class="nav-link" @click="goPage('batch-mgmt')">分单管理</text>
        <text class="nav-link" @click="goPage('summary')">汇总</text>
        <text class="nav-link" @click="goPage('employees')">人员</text>
        <text class="nav-link" @click="goPage('batch-list')">批次</text>
      </view>
      <text class="nav-user">{{ user.display_name }}</text>
      <button class="btn btn-sm btn-danger" @click="logout" style="font-size:11px;padding:2px 6px;margin-left:4px">退</button>
    </view>

    <view class="stats-row">
      <view class="stat-card">
        <text class="stat-num">{{ stats.totalBatches }}</text>
        <text class="stat-label">总批</text>
      </view>
      <view class="stat-card">
        <text class="stat-num">{{ stats.totalItems }}</text>
        <text class="stat-label">最新货</text>
        <text class="stat-batch-name">{{ stats.latestBatchName }}</text>
      </view>
      <view class="stat-card">
        <text class="stat-num warning">{{ stats.pendingItems }}</text>
        <text class="stat-label">待报</text>
        <text class="stat-batch-name">{{ stats.latestBatchName }}</text>
      </view>
      <view class="stat-card">
        <text class="stat-num success">{{ stats.doneItems }}</text>
        <text class="stat-label">已完</text>
        <text class="stat-batch-name">{{ stats.latestBatchName }}</text>
      </view>
    </view>

    <view class="card">
      <text class="card-title">最近批次</text>
      <view v-if="batches.length">
        <view class="list-row header">
          <text class="col-name">批次名称</text>
          <text class="col-time">到货时间</text>
          <text class="col-count">货品</text>
        </view>
        <view v-for="b in batches.slice(0,10)" :key="b.id" class="list-row">
          <text class="col-name">{{ b.name }}</text>
          <text class="col-time">{{ b.arrival_time }}</text>
          <text class="col-count">{{ b.item_count }}</text>
        </view>
      </view>
      <text v-else class="empty-hint">暂无批次</text>
    </view>
  </view>
</template>

<script>
import { loadBatches, loadItems } from "../../utils/admin-api"
import { getStorage, removeStorage } from "../../utils/storage"

export default {
  data() {
    return {
      user: {},
      batches: [],
      items: []
    }
  },
  computed: {
    stats() {
      const totalBatches = this.batches.length
      const sorted = [...this.batches].sort((a, b) => {
        const da = a.arrival_time || ""
        const db = b.arrival_time || ""
        return db.localeCompare(da) || (b.id - a.id)
      })
      const latestBatch = sorted.length ? sorted[0] : null
      const totalItems = latestBatch ? (latestBatch.item_count || 0) : 0
      const latestBatchName = latestBatch ? latestBatch.name : ""
      let pendingItems = 0, doneItems = 0
      for (const item of this.items) {
        if (item.status === "未报货") pendingItems++
        else if (item.status === "已完成") doneItems++
      }
      return { totalBatches, totalItems, pendingItems, doneItems, latestBatchName }
    }
  },
  async onShow() {
    this.user = getStorage("user") || {}
    await this.loadData()
  },
  methods: {
    goPage(name) {
      uni.navigateTo({ url: "/pages/admin/" + name })
    },
    logout() {
      removeStorage("user")
      removeStorage("token")
      uni.navigateTo({ url: "/pages/login/login", redirect: true })
    },
    async loadData() {
      try {
        this.batches = await loadBatches()
        const sorted = [...this.batches].sort((a,b) => (b.arrival_time||'').localeCompare(a.arrival_time||'') || (b.id-a.id)); if (sorted.length) {
          const latest = sorted[0]
          this.items = await loadItems(latest.id)
        }
      } catch (e) {
        console.error("load dashboard error", e)
      }
    }
  }
}
</script>

<style>
.dashboard-page { padding: 16px; }
.stats-row { display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }
.stat-card {
  flex: 1; min-width: calc(50% - 12px); background: #fff; border-radius: 8px;
  padding: 16px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.stat-num { display: block; font-size: 28px; font-weight: bold; color: #409eff; }
.stat-num.warning { color: #e6a23c; }
.stat-num.success { color: #67c23a; }
.stat-label { display: block; font-size: 13px; color: #999; margin-top: 4px; }
.stat-batch-name {
  display: block; font-size: 11px; color: #909399; margin-top: 2px;
  max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.card { background: #fff; border-radius: 8px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.card-title { display: block; font-size: 16px; font-weight: 600; margin-bottom: 12px; }
.list-row { display: flex; padding: 10px 0; border-bottom: 1px solid #f0f0f0; }
.list-row.header { font-weight: 600; color: #666; font-size: 13px; }
.col-name { flex: 1; }
.col-time { width: 120px; text-align: center; }
.col-count { width: 60px; text-align: center; }
.empty-hint { display: block; text-align: center; color: #909399; padding: 20px; font-size: 14px; }
.nav-header { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; padding: 10px 0; border-bottom: 1px solid #e0e0e0; flex-wrap: wrap; }
.nav-title { font-size: 18px; font-weight: bold; color: #303133; margin-right: 4px; }
.nav-menu { display: flex; gap: 6px; flex: 1; }
.nav-link { font-size: 13px; color: #409eff; cursor: pointer; padding: 2px 8px; border-radius: 4px; background: #ecf5ff; white-space: nowrap; }
.nav-user { font-size: 12px; color: #909399; }
.top-bar { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; padding-bottom: 10px; border-bottom: 1px solid #e0e0e0; }
.top-title { flex: 1; font-size: 18px; font-weight: bold; color: #303133; }
.top-user { font-size: 13px; color: #606266; }
.nav-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 16px; }
.nav-card { background: #fff; border-radius: 10px; padding: 14px 8px; text-align: center; box-shadow: 0 2px 6px rgba(0,0,0,0.06); }
.nav-icon { display: block; font-size: 24px; margin-bottom: 4px; }
.nav-label { font-size: 12px; color: #303133; }
</style>