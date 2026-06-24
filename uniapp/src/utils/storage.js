// 本地存储封装 - 条件编译
export function getStorage(key) {
  // #ifdef H5
  try { return JSON.parse(localStorage.getItem(key)) } catch { return null }
  // #endif
  // #ifdef MP-WEIXIN
  const val = uni.getStorageSync(key)
  if (!val) return null
  try { return JSON.parse(val) } catch { return val }
  // #endif
}

export function setStorage(key, value) {
  // #ifdef H5
  localStorage.setItem(key, JSON.stringify(value))
  // #endif
  // #ifdef MP-WEIXIN
  uni.setStorageSync(key, JSON.stringify(value))
  // #endif
}

export function removeStorage(key) {
  // #ifdef H5
  localStorage.removeItem(key)
  // #endif
  // #ifdef MP-WEIXIN
  uni.removeStorageSync(key)
  // #endif
}