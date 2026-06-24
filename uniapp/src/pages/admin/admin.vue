<template>
  <view class="menu-page">
    <view class="menu-header">
      <text class="menu-title">分单系统</text>
      <text class="menu-user" v-if="user.display_name">{{ user.display_name }}</text>
      <button class="btn btn-sm btn-danger" @click="logout">退出</button>
    </view>

    <view class="menu-grid">
      <view class="menu-card" @click="goPage('dashboard')">
        <text class="menu-icon">🏔</text>
        <text class="menu-label">首页概览</text>
      </view>
      <view class="menu-card" @click="goPage('batch-mgmt')">
        <text class="menu-icon">📌</text>
        <text class="menu-label">分单管理</text>
      </view>
      <view class="menu-card" @click="goPage('batch-list')">
        <text class="menu-icon">📋</text>
        <text class="menu-label">分单批次</text>
      </view>
      <view class="menu-card" @click="goPage('summary')">
        <text class="menu-icon">📊</text>
        <text class="menu-label">全品类汇总</text>
      </view>
      <view class="menu-card menu-section">
        <text class="menu-section-title">基础信息</text>
      </view>
      <view class="menu-card" @click="goPage('cargo-types')">
        <text class="menu-icon">📦</text>
        <text class="menu-label">货品种类</text>
      </view>
      <view class="menu-card" @click="goPage('employees')">
        <text class="menu-icon">👥</text>
        <text class="menu-label">人员管理</text>
      </view>
      <view class="menu-card" @click="goPage('units')">
        <text class="menu-icon">⚖️</text>
        <text class="menu-label">单位管理</text>
      </view>
    </view>
  </view>
</template>

<script>
import { getStorage, setStorage } from '../../utils/storage'

export default {
  data() {
    return { user: {} }
  },
  onShow() {
    this.user = getStorage('user') || {}
    if (!this.user || !this.user.id) {
      uni.navigateTo({ url: '/pages/login/login', redirect: true })
    }
  },
  methods: {
    goPage(name) {
      uni.navigateTo({ url: '/pages/admin/' + name + '?from=menu' })
    },
    logout() {
      setStorage('user', null)
      uni.navigateTo({ url: '/pages/login/login', redirect: true })
    }
  }
}
</script>

<style>
.menu-page { padding: 16px; min-height: 100vh; background: #f5f6fa; }
.menu-header { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; padding-bottom: 16px; border-bottom: 1px solid #e0e0e0; }
.menu-title { font-size: 20px; font-weight: bold; color: #303133; flex: 1; }
.menu-user { font-size: 13px; color: #606266; }
.menu-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.menu-card { background: #fff; border-radius: 12px; padding: 20px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.menu-card.menu-section { grid-column: 1 / -1; background: transparent; box-shadow: none; padding: 8px 4px 0; text-align: left; }
.menu-section-title { font-size: 14px; font-weight: 600; color: #909399; }
.menu-icon { display: block; font-size: 32px; margin-bottom: 8px; }
.menu-label { font-size: 14px; color: #303133; }
.btn { display: inline-block; padding: 6px 14px; border: 1px solid #dcdfe6; border-radius: 4px; background: #fff; font-size: 13px; }
.btn-sm { padding: 4px 10px; font-size: 12px; }
.btn-danger { background: #f56c6c; border-color: #f56c6c; color: #fff; }
</style>
