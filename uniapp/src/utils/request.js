// API 请求封装 - 条件编译处理 H5 和 小程序差异
const API = "http://localhost:5000/api"

export async function apiGet(path) {
  // #ifdef H5
  const res = await fetch(API + path)
  if (!res.ok) throw new Error(await res.text())
  return await res.json()
  // #endif

  // #ifdef MP-WEIXIN
  const res = await uni.request({ url: API + path })
  if (res.statusCode >= 400) {
    const msg = (res.data && res.data.error) || ("请求失败: " + res.statusCode)
    throw new Error(msg)
  }
  return res.data
  // #endif
}

export async function apiPost(path, data) {
  // #ifdef H5
  const res = await fetch(API + path, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  })
  if (!res.ok) throw new Error(await res.text())
  return await res.json()
  // #endif

  // #ifdef MP-WEIXIN
  const res = await uni.request({
    url: API + path, method: "POST",
    data, header: { "Content-Type": "application/json" }
  })
  if (res.statusCode >= 400) {
    const msg = (res.data && res.data.error) || ("请求失败: " + res.statusCode)
    throw new Error(msg)
  }
  return res.data
  // #endif
}

export async function apiPut(path, data) {
  // #ifdef H5
  const res = await fetch(API + path, {
    method: "PUT", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  })
  if (!res.ok) throw new Error(await res.text())
  return await res.json()
  // #endif

  // #ifdef MP-WEIXIN
  const res = await uni.request({
    url: API + path, method: "PUT",
    data, header: { "Content-Type": "application/json" }
  })
  if (res.statusCode >= 400) {
    const msg = (res.data && res.data.error) || ("请求失败: " + res.statusCode)
    throw new Error(msg)
  }
  return res.data
  // #endif
}

export async function apiDelete(path) {
  // #ifdef H5
  const res = await fetch(API + path, { method: "DELETE" })
  if (!res.ok) throw new Error(await res.text())
  return await res.json()
  // #endif

  // #ifdef MP-WEIXIN
  const res = await uni.request({ url: API + path, method: "DELETE" })
  if (res.statusCode >= 400) {
    const msg = (res.data && res.data.error) || ("请求失败: " + res.statusCode)
    throw new Error(msg)
  }
  return res.data
  // #endif
}
