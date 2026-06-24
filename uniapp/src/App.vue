<template>
  <page-meta>
    <navigation-bar front-color="#ffffff" background-color="#1e2a3a" />
  </page-meta>
  <view class="app-root">
    <router-view />
  </view>
</template>

<script>
export default {
  onLaunch() {
    console.log("App Launch")
  }
}
</script>

<style>
/* 全局样式 - 从原 style.css 移植 */
view, text, scroll-view { box-sizing: border-box; }
page { background: #f5f6fa; color: #333; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
</style>