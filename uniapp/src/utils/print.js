// 打印功能封装 - 条件编译
export function printSummaryTable(summaryData) {
  // #ifdef H5
  const table = document.getElementById("summary-table")
  if (!table) return
  const win = window.open("", "_blank")
  if (!win) return
  const title = summaryData.batch_name || "全品类汇总"
  const arrival = summaryData.arrival_time || ""
  win.document.write(`<html><head><meta charset="UTF-8">`)
  win.document.write(`<style>@page{size:landscape}body{font-family:sans-serif;padding:20px}h2{text-align:center;font-size:16px;margin-bottom:8px}p{text-align:center;font-size:12px;color:#666;margin-bottom:12px}table{width:100%;border-collapse:collapse;font-size:12px}th,td{border:1px solid #000;padding:3px 4px;text-align:center;font-size:11px}th{background:#d9e1f2;font-weight:700}td{vertical-align:middle}</style></head><body>`)
  win.document.write(`<h2>${title}</h2>`)
  win.document.write(arrival ? `<p>到货时间: ${arrival}</p>` : "")
  win.document.write(table.outerHTML)
  win.document.write(`</body></html>`)
  win.document.close()
  setTimeout(() => { win.print(); win.close() }, 300)
  // #endif

  // #ifdef MP-WEIXIN
  uni.showToast({ title: "长按表格区域截图保存", icon: "none" })
  // #endif
}