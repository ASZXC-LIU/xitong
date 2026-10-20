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
    // #ifdef MP-WEIXIN
    // 微信隐私接口会在需要时要求用户先阅读并同意隐私指引。
    // 由登录页中带有该 id 的官方授权按钮承接此流程。
    if (typeof wx !== "undefined" && typeof wx.onNeedPrivacyAuthorization === "function") {
      wx.onNeedPrivacyAuthorization((resolve) => {
        resolve({ buttonId: "privacy-authorize-button" })
      })
    }
    // #endif
  }
}
</script>

<style>
/* 全局样式 - 从原 style.css 移植 */
view, text, scroll-view { box-sizing: border-box; }
page { background: #f5f6fa; color: #333; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
</style>
