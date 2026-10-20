// API 请求封装 - 复用现有条件编译结构，地址由环境配置提供。
import { getStorage, removeStorage } from "./storage"

const API = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "")

function buildUrl(path) {
  if (!API) throw new Error("未配置 VITE_API_BASE_URL")
  return API + path
}

function requestHeaders(extra = {}) {
  const token = getStorage("token")
  return token ? { ...extra, Authorization: "Bearer " + token } : extra
}

function handleUnauthorized(status) {
  if (status !== 401) return
  removeStorage("token")
  removeStorage("user")
  // #ifdef MP-WEIXIN
  uni.reLaunch({ url: "/pages/login/login" })
  // #endif
}

export async function apiGet(path) {
  // #ifdef H5
  const res = await fetch(buildUrl(path), { headers: requestHeaders() })
  const data = await res.json().catch(() => ({}))
  handleUnauthorized(res.status)
  if (!res.ok) throw new Error(data.error || "请求失败")
  return data
  // #endif

  // #ifdef MP-WEIXIN
  const res = await uni.request({ url: buildUrl(path), header: requestHeaders() })
  handleUnauthorized(res.statusCode)
  if (res.statusCode >= 400) {
    const msg = (res.data && res.data.error) || ("请求失败: " + res.statusCode)
    throw new Error(msg)
  }
  return res.data
  // #endif
}

export async function apiPost(path, data) {
  // #ifdef H5
  const res = await fetch(buildUrl(path), {
    method: "POST", headers: requestHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(data)
  })
  const payload = await res.json().catch(() => ({}))
  handleUnauthorized(res.status)
  if (!res.ok) throw new Error(payload.error || "请求失败")
  return payload
  // #endif

  // #ifdef MP-WEIXIN
  const res = await uni.request({
    url: buildUrl(path), method: "POST",
    data, header: requestHeaders({ "Content-Type": "application/json" })
  })
  handleUnauthorized(res.statusCode)
  if (res.statusCode >= 400) {
    const msg = (res.data && res.data.error) || ("请求失败: " + res.statusCode)
    throw new Error(msg)
  }
  return res.data
  // #endif
}

export async function apiPut(path, data) {
  // #ifdef H5
  const res = await fetch(buildUrl(path), {
    method: "PUT", headers: requestHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(data)
  })
  const payload = await res.json().catch(() => ({}))
  handleUnauthorized(res.status)
  if (!res.ok) throw new Error(payload.error || "请求失败")
  return payload
  // #endif

  // #ifdef MP-WEIXIN
  const res = await uni.request({
    url: buildUrl(path), method: "PUT",
    data, header: requestHeaders({ "Content-Type": "application/json" })
  })
  handleUnauthorized(res.statusCode)
  if (res.statusCode >= 400) {
    const msg = (res.data && res.data.error) || ("请求失败: " + res.statusCode)
    throw new Error(msg)
  }
  return res.data
  // #endif
}

export async function apiDelete(path) {
  // #ifdef H5
  const res = await fetch(buildUrl(path), { method: "DELETE", headers: requestHeaders() })
  const data = await res.json().catch(() => ({}))
  handleUnauthorized(res.status)
  if (!res.ok) throw new Error(data.error || "请求失败")
  return data
  // #endif

  // #ifdef MP-WEIXIN
  const res = await uni.request({ url: buildUrl(path), method: "DELETE", header: requestHeaders() })
  handleUnauthorized(res.statusCode)
  if (res.statusCode >= 400) {
    const msg = (res.data && res.data.error) || ("请求失败: " + res.statusCode)
    throw new Error(msg)
  }
  return res.data
  // #endif
}
