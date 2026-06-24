<template>
  <div class="admin-layout">
    <!-- ========== 左侧菜单 ========== -->
    <aside class="sidebar" :class="{ open: sidebarOpen }" @click.self="sidebarOpen=false">
      <div class="sidebar-logo">
        <span>分单系统</span>
        <button class="hamburger" @click.stop="sidebarOpen=!sidebarOpen">{{ sidebarOpen ? "✕" : "☰" }}</button>
      </div>
      <nav class="sidebar-nav" @click.stop>
        <a :class="{ active: currentPage==='dashboard' }" @click="goToDashboard">首页概览</a>
        <a :class="{ active: currentPage==='batches' }" @click="goToBatches">分单管理</a>
        <a :class="{ active: currentPage==='batchList' }" @click="currentPage='batchList'; loadBatches()">分单批次</a>
        <div class="sidebar-section-label">基础信息</div>
        <a :class="{ active: currentPage==='cargoTypes' }" @click="currentPage='cargoTypes'">货品种类</a>
        <a :class="{ active: currentPage==='employeeMgmt' }" @click="currentPage='employeeMgmt'">人员管理</a>
        <a :class="{ active: currentPage==='unitTypes' }" @click="currentPage='unitTypes'">单位管理</a>
        <a :class="{ active: currentPage==='summary' }" @click="openSummary">全品类汇总</a>
      </nav>
      <div class="sidebar-footer" @click.stop>
        <span>{{ user.display_name }}</span>
        <button class="btn btn-sm btn-danger" @click="logout">退</button>
      </div>
    </aside>

    <!-- ========== 右侧内容 ========== -->
    <main class="main-content" @click="sidebarOpen=false">
      <div class="mobile-header">
        <button class="hamburger" @click.stop="sidebarOpen=!sidebarOpen">{{ sidebarOpen ? "✕" : "☰" }}</button>
        <span class="mobile-title">{{ mobilePageTitle }}</span>
      </div>

      <!-- 首页概览 -->
      <div v-if="currentPage==='dashboard'">
        <h2 class="page-title">首页概览</h2>
        <div class="stats-row">
          <div class="stat-card"><div class="stat-num">{{ stats.totalBatches }}</div><div class="stat-label">总批</div></div>
          <div class="stat-card">
            <div class="stat-num">{{ stats.totalItems }}</div>
            <div class="stat-label">最新货</div>
            <div style="font-size:11px;color:#909399;margin-top:2px;max-width:140px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" :title="stats.latestBatchName">{{ stats.latestBatchName }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-num" style="color:#e6a23c">{{ stats.pendingItems }}</div>
            <div class="stat-label">待报</div>
            <div style="font-size:11px;color:#909399;margin-top:2px;max-width:140px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" :title="stats.latestBatchName">{{ stats.latestBatchName }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-num" style="color:#67c23a">{{ stats.doneItems }}</div>
            <div class="stat-label">已完</div>
            <div style="font-size:11px;color:#909399;margin-top:2px;max-width:140px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" :title="stats.latestBatchName">{{ stats.latestBatchName }}</div>
          </div>
        </div>
        <div class="card">
          <table v-if="batches.length">
            <thead><tr><th>批次名称</th><th>到货时间</th><th>货品</th><th>创建时间</th></tr></thead>
            <tbody>
              <tr v-for="b in batches.slice(0,10)" :key="b.id">
                <td>{{ b.name }}</td><td>{{ b.arrival_time }}</td><td>{{ b.item_count }}</td><td>{{ b.created_at }}</td>
              </tr>
            </tbody>
          </table>
          <p v-else style="color:#999;text-align:center;padding:20px">暂无批次</p>
        </div>
      </div>

      <!-- 分单管理 -->
      <div v-if="currentPage==='batches'">
        <h2 class="page-title">分单管理</h2>
        <div class="batch-layout">
          <!-- 批次选择下拉栏 -->
          <div class="batch-select-bar">
            <label style="font-weight:600;margin-right:8px;white-space:nowrap">选择批次:</label>
            <select v-model="selectedBatchId" @change="onBatchSelectChange" class="batch-select">
              <option value="" disabled>-- 请选择批次 --</option>
              <option v-for="b in sortedBatches" :key="b.id" :value="b.id">
                {{ b.name }} (到货: {{ b.arrival_time }} | {{ b.item_count }} 个货)
              </option>
            </select>
            <button class="btn btn-sm btn-primary" @click="showBatchForm=true" style="margin-left:10px">+ 新建</button>
            <button class="btn btn-sm" @click="openReportForSelected" style="margin-left:6px" :disabled="!selectedBatchId">明细</button>
            <button class="btn btn-sm btn-danger" @click="deleteBatch(selectedBatchId)" style="margin-left:6px" :disabled="!selectedBatchId">删除</button>
          </div>

          <!-- 右：货品表格 -->
          <div class="batch-right">
            <div v-if="!selectedBatchId" class="empty-hint">请选择一个批次</div>
            <template v-else>
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
                <strong>货品列表</strong>
                <button class="btn btn-sm btn-primary" @click="showItemForm=true">+ 添加货品</button>
              </div>
              <div v-if="items.length===0" class="empty-hint">暂无货品</div>
              <div v-else class="matrix-table-wrap">
                <table class="matrix-table">
                  <thead>
                    <tr>
                      <th class="col-name">货品名称</th>
                      <th class="col-unit">单位</th>
                      <th v-for="emp in matrixEmployees" :key="emp.id" class="col-emp" colspan="2">
                        <div class="emp-header-name">{{ emp.name }}</div>
                        <div class="emp-header-sub"><span class="sum-sub-alloc">分配</span><span class="sum-sub-div">/</span><span class="sum-sub-actual">报货</span></div>
                      </th>
                      <th class="col-total">总分配</th>
                      <th class="col-total">总报货</th>
                      <th class="col-status">状态</th>
                      <th class="col-remark">备注</th>
                      <th class="col-actions">操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="item in items" :key="item.id">
                      <td class="item-name-cell" @click="showItemDetail(item)"><strong>{{ item.name }}</strong></td>
                      <td>{{ item.unit }}</td>
                      <template v-for="emp in matrixEmployees" :key="emp.id">
                        <td class="cell-qty-alloc">
                          <input type="number"
                                 :value="getItemQty(item, emp.id)"
                                 @change="saveEdit(item, emp.id, $event.target.value)"
                                 step="any" min="0" class="cell-input" />
                        </td>
                        <td class="cell-qty-actual">
                          <span class="actual-qty">{{ getItemActual(item, emp.id) }}</span>
                        </td>
                      </template>
                      <td class="cell-total">{{ getItemTotal(item) }}</td>
                      <td class="cell-total cell-total-actual">{{ getItemActualTotal(item) }}</td>
                      <td><span :class="'status-badge ' + (item.status==='未分配' ? 'status-pending' : item.status==='未报货' ? 'status-warn' : 'status-ok')">{{ item.status }}</span></td>
                      <td class="cell-remark">{{ item.remark || '无备注' }}</td>
                      <td>
                        <div class="action-group">
                          <button class="btn btn-xs btn-danger" @click="deleteItem(item.id)" title="删除此货物">删除</button>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                  <tfoot v-if="items.length > 1">
                    <tr>
                      <td><strong>合计</strong></td>
                      <td></td>
                      <template v-for="emp in matrixEmployees" :key="emp.id">
                        <td class="cell-total">{{ getColumnTotal(emp.id) }}</td>
                        <td class="cell-total cell-total-actual">{{ getMatrixColumnActualTotal(emp.id) }}</td>
                      </template>
                      <td class="cell-total">{{ getGrandTotal() }}</td>
                      <td class="cell-total cell-total-actual">{{ getMatrixGrandActualTotal() }}</td>
                      <td></td>
                      <td></td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </template>
          </div>
        </div>
      </div>

      <!-- 货品种类管理 -->
      <div v-if="currentPage==='cargoTypes'">
        <h2 class="page-title">货品种类管理</h2>
        <div class="card">
          <div style="display:flex;gap:8px;margin-bottom:12px">
            <input v-model="cargoForm.name" placeholder="种类名称" style="max-width:200px" />
            <input v-model="cargoForm.default_unit" list="default-unit-list" placeholder="默认单位" style="max-width:200px" autocomplete="off" />
            <datalist id="default-unit-list">
              <option v-for="ut in unitTypes" :key="ut.id" :value="ut.name">{{ ut.name }}</option>
            </datalist>
            <button class="btn btn-primary btn-sm" @click="addCargoType">添加</button>
          </div>
          <p v-if="cargoMsg" style="color:#67c23a">{{ cargoMsg }}</p>
          <table class="data-table">
            <thead><tr><th>ID</th><th>种类名称</th><th>默认单位</th><th>操作</th></tr></thead>
            <tbody>
              <tr v-for="ct in cargoTypes" :key="ct.id">
                <td>{{ ct.id }}</td><td>{{ ct.name }}</td><td>{{ ct.default_unit }}</td>
                <td><button class="btn btn-sm btn-danger" @click="deleteCargoType(ct.id)">删除</button></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 人员管理 -->
      <div v-if="currentPage==='employeeMgmt'">
        <h2 class="page-title">人员管理</h2>
        <div class="card">
          <div style="display:flex;gap:8px;margin-bottom:12px">
            <input v-model="empForm.display_name" placeholder="姓名" style="max-width:150px" />
            <input v-model="empForm.username" placeholder="登录名" style="max-width:150px" />
            <input v-model="empForm.password" type="password" placeholder="密码" style="max-width:150px" />
            <button class="btn btn-primary btn-sm" @click="addEmployee">添加</button>
          </div>
          <p v-if="empMsg" style="color:#67c23a">{{ empMsg }}</p>
          <table class="data-table">
            <thead><tr><th>ID</th><th>姓名</th><th>登录</th><th>角色</th><th>操作</th></tr></thead>
            <tbody>
              <tr v-for="e in employees" :key="e.id">
                <td>{{ e.id }}</td><td>{{ e.display_name }}</td><td>{{ e.username }}</td><td>{{ e.role }}</td>
                <td><button class="btn btn-sm btn-danger" @click="deleteEmployee(e.id)">删除</button></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 单位管理 -->
      <div v-if="currentPage==='unitTypes'">
        <h2 class="page-title">单位管理</h2>
        <div class="card">
          <div style="display:flex;gap:8px;margin-bottom:12px">
            <input v-model="unitForm.name" placeholder="单位名称" style="max-width:200px" />
            <button class="btn btn-primary btn-sm" @click="addUnitType">添加</button>
          </div>
          <p v-if="unitMsg" style="color:#67c23a">{{ unitMsg }}</p>
          <table class="data-table">
            <thead><tr><th>ID</th><th>单位名称</th><th>操作</th></tr></thead>
            <tbody>
              <tr v-for="ut in unitTypes" :key="ut.id">
                <td>{{ ut.id }}</td><td>{{ ut.name }}</td>
                <td>
                  <button class="btn btn-sm" @click="editUnitType(ut)">编辑</button>
                  <button class="btn btn-sm btn-danger" @click="deleteUnitType(ut.id)">删除</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 全品类汇总-->
      <div v-if="currentPage==='summary'">
        <h2 class="page-title">全品类汇总</h2>
        <div class="card no-print" style="display:flex;gap:8px;align-items:center;margin-bottom:16px;flex-wrap:wrap">
          <div style="display:flex;align-items:center;gap:8px;flex:1;min-width:200px">
            <label style="font-weight:600;white-space:nowrap;font-size:14px">选择批次:</label>
            <select v-model="summaryBatchId" @change="onSummaryBatchChange" class="batch-select" style="max-width:300px">
              <option value="">-- 请选择批次 --</option>
              <option v-for="b in sortedBatches" :key="b.id" :value="b.id">
                {{ b.name }} ({{ b.arrival_time }})
              </option>
            </select>
          </div>
          <button class="btn btn-primary btn-sm" @click="printPage" :disabled="!summaryData">打印</button>
          <button class="btn btn-sm" @click="downloadExcel" :disabled="!summaryData" style="background:#67c23a;color:#fff;border-color:#67c23a">下载Excel</button>
        </div>
        <div v-if="!summaryData" style="text-align:center;color:#999;padding:60px 20px;font-size:15px">请从分单批次或分单管理中选择一个批次查看汇总</div>
        <div v-else id="print-zone">
          <table class="summary-table" id="summary-table">
            <thead>
              <tr>
                <th class="sum-col-idx">序号</th>
                <th class="sum-col-name">货品名称</th>
                <th class="sum-col-unit">单位</th>
                <th v-for="emp in summaryEmployees" :key="emp.id" class="sum-col-emp" colspan="2">
                  <div class="sum-emp-name">{{ emp.name }}</div>
                  <div class="sum-emp-sub">
                    <span class="sum-sub-alloc">分货</span>
                    <span class="sum-sub-div">/</span>
                    <span class="sum-sub-actual">报货</span>
                  </div>
                </th>
                <th class="sum-col-total">总分配</th>
                <th class="sum-col-total">总报货</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(d, idx) in summaryData.details" :key="d.item_name">
                <td class="sum-idx">{{ idx + 1 }}</td>
                <td class="sum-name">{{ d.item_name }}</td>
                <td class="sum-unit">{{ d.item_unit }}</td>
                <template v-for="emp in summaryEmployees" :key="emp.id">
                  <td class="sum-cell sum-cell-alloc">{{ getAlloc(d, emp.id) }}</td>
                  <td class="sum-cell sum-cell-actual">{{ getActual(d, emp.id) }}</td>
                </template>
                <td class="sum-total sum-total-alloc">{{ getAllocTotal(d) }}</td>
                <td class="sum-total sum-total-actual">{{ d.total_actual ?? 0 }}</td>
              </tr>
            </tbody>
            <tfoot>
              <tr>
                <td></td>
                <td style="text-align:center;font-weight:600;padding:8px 10px">合计</td>
                <td></td>
                <template v-for="emp in summaryEmployees" :key="emp.id">
                  <td class="sum-total sum-total-alloc">{{ getColumnAllocTotal(emp.id) }}</td>
                  <td class="sum-total sum-total-actual">{{ getColumnActualTotal(emp.id) }}</td>
                </template>
                <td class="sum-total sum-total-alloc">{{ getGrandAllocTotal() }}</td>
                <td class="sum-total sum-total-actual">{{ getGrandActualTotal() }}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>


      <!-- 分单批次列表 -->
      <div v-if="currentPage==='batchList'" class="batch-list-page">
        <h2 class="page-title">分单批次</h2>
        <div class="card">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
            <span style="color:#909399;font-size:14px">{{ batches.length }} 个批次</span>
            <button class="btn btn-primary btn-sm" @click="showBatchFormForCreate">+ 新建批次</button>
          </div>
          <table v-if="batches.length" class="data-table">
            <thead>
              <tr>
                <th>名称</th>
                <th>到货时间</th>
                <th>货品数</th>
                <th>备注</th>
                <th>创建时间</th>
                <th style="width:240px">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="b in sortedBatches" :key="b.id">
                <td><strong>{{ b.name }}</strong></td>
                <td>{{ b.arrival_time }}</td>
                <td>{{ b.item_count }}</td>
                <td class="cell-remark">{{ b.batch_remark || '无备注' }}</td>
                <td>{{ b.created_at?.slice(0,16) }}</td>
                <td>
                  <div class="action-group" style="display:flex;gap:4px;flex-wrap:nowrap">
                    <button class="btn btn-xs btn-primary" @click="goToBatchManagement(b)">分单</button>
                    <button class="btn btn-xs" @click="editBatch(b)">编辑</button>
                    <button class="btn btn-xs btn-danger" @click="deleteBatch(b.id)">删除</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
          <p v-else style="text-align:center;color:#999;padding:40px">暂无批次</p>
        </div>
      </div>
    </main>

    <!-- 新建批次弹窗 -->
    <div v-if="showBatchForm" class="modal-mask" @click.self="showBatchForm=false">
      <div class="modal-card">
        <h3>{{ editingBatchId ? '编辑批次' : '新建报货批次' }}</h3>
        <div class="form-group">
          <label>报货日期</label>
          <input type="date" v-model="batchForm.batch_date" />
        </div>
        <div class="form-group">
          <label>到货时间</label>
          <input type="date" v-model="batchForm.arrival_time" />
        </div>
        <div class="form-group">
          <label>批号备注</label>
          <input v-model="batchForm.batch_remark" placeholder="备注信息（可选）" />
        </div>
        <div class="modal-actions">
          <button class="btn" @click="showBatchForm=false">取消</button>
          <button class="btn btn-primary" @click="editingBatchId ? updateBatch() : createBatch()">{{ editingBatchId ? '保存' : '创建' }}</button>
        </div>
        <p v-if="batchMsg" :style="batchMsgOk ? 'color:#67c23a' : 'color:#f56c6c'">{{ batchMsg }}</p>
      </div>
    </div>


    <!-- 添加货品弹窗 -->
    <div v-if="showItemForm" class="modal-mask" @click.self="showItemForm=false">
      <div class="modal-card">
        <h3>添加货品</h3>
        <div class="form-group">
          <label>货品名称</label>
          <input v-model="itemForm.name" list="cargo-names" placeholder="输入或选择种类..." @input="onCargoNameInput" autocomplete="off" />
          <datalist id="cargo-names">
            <option v-for="ct in cargoTypes" :key="ct.id" :value="ct.name">{{ ct.name }}</option>
          </datalist>
        </div>
        <div class="form-group">
          <label>单位</label>
          <input v-model="itemForm.unit" placeholder="自动填入默认单位" readonly style="background:#f5f7fa;color:#666;cursor:default" />
        </div>
        <div class="form-group">
          <label>备注</label>
          <input v-model="itemForm.remark" placeholder="备注信息（可选）" />
        </div>
        <div class="modal-actions">
          <button class="btn" @click="showItemForm=false">取消</button>
          <button class="btn btn-primary" @click="addItem">添加</button>
        </div>
      </div>
    </div>

    <!-- 分配弹窗 -->
    <div v-if="showAssignmentModal" class="modal-mask" @click.self="showAssignmentModal=false">
      <div class="modal-card">
        <h3>分配货品: {{ assignItem.name }}</h3>
        <div v-for="(a, idx) in assignmentForm" :key="idx" style="display:flex;gap:8px;margin-bottom:8px">
          <select v-model="a.user_id" style="flex:1">
            <option value="">-- 选择员工 --</option>
            <option v-for="e in employees" :key="e.id" :value="e.id">{{ e.display_name }}</option>
          </select>
          <input v-model="a.allocated_quantity" type="number" step="0.1" placeholder="数量" style="width:100px" />
          <button class="btn btn-sm btn-danger" @click="removeAssignmentRow(idx)" v-if="idx>0"></button>
        </div>
        <button class="btn btn-sm" @click="addAssignmentRow" style="margin-bottom:12px">+ 添加分配</button>
        <div class="modal-actions">
          <button class="btn" @click="showAssignmentModal=false">取消</button>
          <button class="btn btn-primary" @click="saveAssignment">保存</button>
        </div>
        <p v-if="assignMsg" style="color:#67c23a">{{ assignMsg }}</p>
      </div>
    </div>

      <!-- 手机端货品详情弹窗 -->
    <div v-if="itemDetailView" class="modal-mask" @click.self="itemDetailView=null">
      <div class="modal-card modal-card-wide">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
          <h3 style="margin:0">{{ itemDetailView.name }}</h3>
          <button class="btn btn-sm" @click="itemDetailView=null">关闭</button>
        </div>
        <div style="margin-bottom:12px;font-size:13px;color:#909399;display:flex;gap:16px;flex-wrap:wrap">
          <span>单位: {{ itemDetailView.unit }}</span>
          <span>规格: {{ itemDetailView.spec || '无' }}</span>
          <span>备注: {{ itemDetailView.remark || '无' }}</span>
          <span :class="'status-badge ' + (itemDetailView.status==='未分配' ? 'status-pending' : itemDetailView.status==='未报货' ? 'status-warn' : 'status-ok')">{{ itemDetailView.status }}</span>
        </div>
        <div v-if="employees && employees.length" class="mobile-assign-list">
          <div class="assign-header" style="display:flex;font-weight:600;font-size:13px;color:#666;padding:8px 0;border-bottom:1px solid #eee">
            <span style="flex:1">员工</span>
            <span style="width:80px;text-align:center">分配数量</span>
            <span style="width:80px;text-align:center">已报数量</span>
          </div>
          <div v-for="emp in employees" :key="emp.id" class="assign-row" style="display:flex;align-items:center;padding:10px 0;border-bottom:1px solid #f0f0f0">
            <span style="flex:1;font-weight:500">{{ emp.display_name || emp.name }}</span>
            <span style="width:80px;text-align:center">
              <input type="number" :value="getItemQty(itemDetailView, emp.id)"
                     @change="saveEdit(itemDetailView, emp.id, $event.target.value)"
                     step="any" min="0" class="cell-input" />
            </span>
            <span style="width:80px;text-align:center;color:#67c23a;font-weight:500">{{ getItemActual(itemDetailView, emp.id) }}</span>
          </div>
        </div>
        <div v-if="employees && employees.length" style="margin-top:12px;padding-top:12px;border-top:2px solid #409eff;display:flex;justify-content:space-between;font-weight:600;font-size:14px">
          <span>合计</span>
          <div style="display:flex;gap:24px">
            <span style="color:#e6a23c">分配: {{ getItemTotal(itemDetailView) }}</span>
            <span style="color:#67c23a">报货: {{ getItemActualTotal(itemDetailView) }}</span>
          </div>
        </div>
      </div>
    </div>

</div>
</template>

<script>
const API = "http://localhost:5000/api"

async function apiGet(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error((await r.json()).error || r.statusText);
  return r.json();
}

async function apiPost(url, body) {
  const r = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  if (!r.ok) throw new Error((await r.json()).error || r.statusText);
  return r.json();
}

async function apiPut(url, body) {
  const r = await fetch(url, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  if (!r.ok) throw new Error((await r.json()).error || r.statusText);
  return r.json();
}

async function apiDelete(url) {
  const r = await fetch(url, { method: "DELETE" });
  if (!r.ok) throw new Error((await r.json()).error || r.statusText);
  return r.json();
}

export default {
  data() {
    return {
      user: JSON.parse(localStorage.getItem("user") || "{}"),
      currentPage: "dashboard",
      batches: [],
      selectedBatchId: null,
      items: [],
      employees: [],
      cargoTypes: [],
      unitTypes: [],
      cargoForm: { name: "", default_unit: "" },
      unitForm: { name: "" },
      empForm: { display_name: "", username: "", password: "" },
      cargoMsg: "", empMsg: "", unitMsg: "",
      showBatchForm: false,
      editingBatchId: null,
      batchForm: { name: "", arrival_time: "", batch_remark: "", batch_date: "" },
      batchMsg: "", batchMsgOk: false,
      showItemForm: false,
      itemForm: { name: "", spec: "", unit: "", remark: "" },
      showAssignmentModal: false,
      assignItem: null,
      assignmentForm: [],
      assignMsg: "",
      sidebarOpen: false,
      employeeSearch: "",
      summaryData: null,
      summaryBatchId: null,
      itemDetailView: null,
      mobileItemId: null,
    }
  },
  computed: {
    stats() {
      const totalBatches = this.batches.length
      const latestBatch = this.sortedBatches.length ? this.sortedBatches[0] : null
      const totalItems = latestBatch ? (latestBatch.item_count || 0) : 0
      let pendingItems = 0, doneItems = 0
      for (const item of this.items) {
        if (item.status === "未报货") pendingItems++
        else if (item.status === "已完成") doneItems++
      }
      return { totalBatches, totalItems, pendingItems, doneItems, latestBatchName: latestBatch ? latestBatch.name : '' }
    },
    matrixEmployees() {
      const empMap = {}
      for (const item of this.items) {
        if (item.assignments) {
          for (const a of item.assignments) {
            if (a.user_id && a.user_name) {
              empMap[a.user_id] = { id: a.user_id, name: a.user_name }
            }
          }
        }
      }
      const order = {}
      this.employees.forEach((e, i) => { order[e.id] = i })
      return this.employees.map(e => ({ id: e.id, name: e.display_name || e.name }))
    },
    summaryEmployees() {
      if (!this.employees || !this.employees.length) return []
      return this.employees.map(e => ({ id: e.id, name: e.display_name || e.name }))
    },
    sortedBatches() {
      return [...this.batches].sort((a, b) => {
        const da = a.arrival_time || ''
        const db = b.arrival_time || ''
        return db.localeCompare(da) || (b.id - a.id)
      })
    }
  },
  async mounted() {
    if (!this.user.id) { this.$router.push("/login"); return }
    await Promise.all([
      this.loadBatches(), this.loadEmployees(),
      this.loadCargoTypes(), this.loadUnitTypes()
    ])
  },
  methods: {
    goToBatches() {
      this.currentPage = 'batches'
      if (this.selectedBatchId && this.batches.length) {
        this.selectBatchById(this.selectedBatchId)
      } else if (this.sortedBatches.length) {
        this.selectBatch(this.sortedBatches[0])
      }
    },
    goToDashboard() {
      this.currentPage = 'dashboard'
      if (!this.sortedBatches.length) return
      const latest = this.sortedBatches[0]
      if (this.selectedBatchId !== latest.id) {
        this.selectBatch(latest)
      }
    },
    async loadBatches() {
      try { this.batches = await apiGet(API + "/batches") } catch (e) { console.error("loadBatches", e) }
      if (this.selectedBatchId) { this.selectBatchById(this.selectedBatchId) } else if (this.sortedBatches.length) { this.selectBatch(this.sortedBatches[0]) }
    },
    async loadItems(batchId) {
      try { this.items = await apiGet(API + "/batches/" + batchId + "/items") } catch (e) { console.error("loadItems", e) }
      if (this.items) this.items.forEach(item => { if (!item.assignments) item.assignments = [] })
    },
    async loadEmployees() {
      try { this.employees = await apiGet(API + "/employees") } catch (e) { console.error("loadEmployees", e) }
    },
    async loadCargoTypes() {
      try { this.cargoTypes = await apiGet(API + "/cargo-types") } catch (e) { console.error("loadCargoTypes", e) }
    },
    async loadUnitTypes() {
      try { this.unitTypes = await apiGet(API + "/unit-types") } catch (e) { console.error("loadUnitTypes", e) }
    },
    selectBatch(b) {
      this.selectedBatchId = b.id
      this.loadItems(b.id)
    },
    selectBatchById(id) {
      this.selectedBatchId = id
      this.loadItems(id)
    },
    onBatchSelectChange() {
      const batch = this.batches.find(b => b.id === this.selectedBatchId)
      if (batch) this.selectBatch(batch)
    },
    openReportForSelected() {
      if (!this.selectedBatchId) return
      const batch = this.batches.find(b => b.id === this.selectedBatchId)
      if (batch) this.openReport(batch)
    },
    goToBatchManagement(b) {
      this.currentPage = 'batches'
      this.selectedBatchId = b.id
      this.loadItems(b.id)
    },
    onBatchSelectChange() {
      const batch = this.batches.find(b => b.id === this.selectedBatchId)
      if (batch) this.selectBatch(batch)
    },
    openReportForSelected() {
      if (!this.selectedBatchId) return
      const batch = this.batches.find(b => b.id === this.selectedBatchId)
      if (batch) this.openReport(batch)
    },
    goToBatchManagement(b) {
      this.currentPage = 'batches'
      this.selectedBatchId = b.id
      this.loadItems(b.id)
    },
    showBatchFormForCreate() {
      this.editingBatchId = null
      this.batchForm = { name: "", arrival_time: "", batch_remark: "", batch_date: "" }
      this.batchMsg = ""
      this.showBatchForm = true
    },
    editBatch(b) {
      this.editingBatchId = b.id
      const dateStr = b.arrival_time || ""
      this.batchForm = {
        name: b.name || "",
        arrival_time: b.arrival_time || "",
        batch_remark: b.batch_remark || "",
        batch_date: dateStr
      }
      this.batchMsg = ""
      this.showBatchForm = true
    },
    async updateBatch() {
      try {
        this.batchMsg = ""
        const payload = {
          name: this.batchForm.name || "",
          arrival_time: this.batchForm.arrival_time || "",
          batch_remark: this.batchForm.batch_remark || ""
        }
        await apiPut(API + "/batches/" + this.editingBatchId, payload)
        this.batchMsg = "更新成功!"
        this.batchMsgOk = true
        this.showBatchForm = false
        this.editingBatchId = null
        await this.loadBatches()
      } catch (e) {
        this.batchMsg = e.response?.data?.error || "更新失败"
        this.batchMsgOk = false
      }
    },
    async createBatch() {
      try {
        this.batchMsg = ""
        const dateStr = this.batchForm.batch_date || new Date().toISOString().slice(0,10)
        const parts = dateStr.split("-")
        const month = parseInt(parts[1])
        const day = parseInt(parts[2])
        this.batchForm.name = month + "月" + day + "日报货"
        this.batchForm.arrival_time = dateStr
        const r = await apiPost(API + "/batches", this.batchForm)
        this.batchMsg = "创建成功!"
        this.batchMsgOk = true
        this.showBatchForm = false
        this.editingBatchId = null
        this.batchForm = { name: "", arrival_time: "", batch_remark: "", batch_date: "" }
        await this.loadBatches()
      } catch (e) {
        this.batchMsg = e.response?.data?.error || "创建失败"
        this.batchMsgOk = false
      }
    },
    async deleteBatch(id) {
      if (!confirm("确认删除此批次?")) return
      await apiDelete(API + "/batches/" + id)
      if (this.selectedBatchId === id) { this.selectedBatchId = null; this.items = [] }
      this.loadBatches()
    },
    async addItem() {
      if (!this.itemForm.name) return
      await apiPost(API + "/batches/" + this.selectedBatchId + "/items", this.itemForm)
      this.showItemForm = false
      this.itemForm = { name: "", spec: "", unit: "", remark: "" }
      await this.loadItems(this.selectedBatchId)
      await this.loadBatches()
    },
    async deleteItem(id) {
      if (!confirm("确认删除此货")) return
      await apiDelete(API + "/items/" + id)
      await this.loadItems(this.selectedBatchId)
      await this.loadBatches()
    },
    async saveEdit(item, userId, newValue) {
      const newQty = Number(newValue) || 0
      const existing = item.assignments || []
      let assignments = existing.map(a => ({
        user_id: a.user_id,
        allocated_quantity: a.user_id === userId ? newQty : (a.allocated_quantity || 0)
      }))
      if (!existing.find(a => a.user_id === userId)) {
        assignments.push({ user_id: userId, allocated_quantity: newQty })
      }
      try {
        await apiPut(API + "/items/" + item.id + "/assignments", assignments)
        await this.loadItems(this.selectedBatchId)
      } catch (e) {
        console.error("saveEdit failed", e)
      }
    },
    getItemQty(item, userId) {
      if (!item.assignments) return 0
      const a = item.assignments.find(a => a.user_id === userId)
      return a ? (a.allocated_quantity || 0) : 0
    },
    getItemActual(item, userId) {
      if (!item.assignments) return 0
      const a = item.assignments.find(a => a.user_id === userId)
      return a && a.actual_quantity != null ? a.actual_quantity : 0
    },
    getItemTotal(item) {
      if (!item.assignments) return 0
      return item.assignments.reduce((sum, a) => sum + (a.allocated_quantity || 0), 0)
    },
    getItemActualTotal(item) {
      if (!item.assignments) return 0
      return item.assignments.reduce((sum, a) => sum + (a.actual_quantity || 0), 0)
    },
    getColumnTotal(userId) {
      let total = 0
      for (const item of this.items) {
        if (item.assignments) {
          const a = item.assignments.find(a => a.user_id === userId)
          if (a) total += (a.allocated_quantity || 0)
        }
      }
      return total
    },
    getMatrixColumnActualTotal(userId) {
      let total = 0
      for (const item of this.items) {
        if (item.assignments) {
          const a = item.assignments.find(a => a.user_id === userId)
          if (a) total += (a.actual_quantity || 0)
        }
      }
      return total
    },
    getGrandTotal() {
      let total = 0
      for (const item of this.items) {
        if (item.assignments) {
          for (const a of item.assignments) {
            total += (a.allocated_quantity || 0)
          }
        }
      }
      return total
    },
    getMatrixGrandActualTotal() {
      let total = 0
      for (const item of this.items) {
        if (item.assignments) {
          for (const a of item.assignments) {
            total += (a.actual_quantity || 0)
          }
        }
      }
      return total
    },
    onCargoNameInput() {
      const found = this.cargoTypes.find(c => c.name === this.itemForm.name)
      this.itemForm.unit = found ? found.default_unit || '' : ''
    },
    openAssignment(item) {
      this.assignItem = item
      this.assignMsg = ""
      this.assignmentForm = item.assignments && item.assignments.length
        ? item.assignments.map(a => ({ user_id: a.user_id, allocated_quantity: a.allocated_quantity }))
        : [{ user_id: "", allocated_quantity: "" }]
      this.showAssignmentModal = true
    },
    addAssignmentRow() {
      this.assignmentForm.push({ user_id: "", allocated_quantity: "" })
    },
    removeAssignmentRow(idx) {
      this.assignmentForm.splice(idx, 1)
    },
    async saveAssignment() {
      const payload = this.assignmentForm.filter(a => a.user_id)
        .map(a => ({ user_id: Number(a.user_id), allocated_quantity: Number(a.allocated_quantity) || 0 }))
      await apiPut(API + "/items/" + this.assignItem.id + "/assignments", payload)
      this.assignMsg = "保存成功!"
      await this.loadItems(this.selectedBatchId)
    },
    async openReport(b) {
      this.summaryData = await apiGet(API + "/batches/" + b.id + "/report")
      this.currentPage = "summary"
    },
    async onSummaryBatchChange() {
      this.summaryData = null
      if (this.summaryBatchId) {
        this.summaryData = await apiGet(API + "/batches/" + this.summaryBatchId + "/report")
      }
    },
    async openSummary() {
      this.summaryData = null
      this.summaryBatchId = null
      if (this.batches.length) {
        this.summaryBatchId = this.sortedBatches[0].id
        this.summaryData = await apiGet(API + "/batches/" + this.batches[0].id + "/report")
      }
      this.currentPage = "summary"
    },
        printPage() {
      if (!this.summaryData) return
      const table = document.getElementById("summary-table")
      if (!table) return
      const win = window.open("", "_blank")
      if (!win) return
      const title = this.summaryData.batch_name || "全品类汇总"
      const arrival = this.summaryData.arrival_time || ""
      win.document.write('<html><head><meta charset="UTF-8">')
      win.document.write("<style>@page{size:landscape}body{font-family:sans-serif;padding:20px}h2{text-align:center;font-size:16px;margin-bottom:8px}p{text-align:center;font-size:12px;color:#666;margin-bottom:12px}table{width:100%;border-collapse:collapse;font-size:12px}th,td{border:1px solid #000;padding:3px 4px;text-align:center;font-size:11px}th{background:#d9e1f2;font-weight:700}td{vertical-align:middle}.sum-name{text-align:left}.sum-total{font-weight:600}</style></head><body>")
      win.document.write("<h2>" + title + "</h2>")
      win.document.write("<p>" + (arrival ? "到货时间: " + arrival : "") + "</p>")
      win.document.write(table.outerHTML)
      win.document.write("</body></html>")
      win.document.close()
      setTimeout(() => { win.print(); win.close() }, 300)
    },
    async addCargoType() {
      if (!this.cargoForm.name) return
      await apiPost(API + "/cargo-types", this.cargoForm)
      this.cargoForm = { name: "", default_unit: "" }
      this.cargoMsg = "添加成功"
      this.loadCargoTypes()
    },
    async deleteCargoType(id) {
      if (!confirm("确认删除?")) return
      await apiDelete(API + "/cargo-types/" + id)
      this.loadCargoTypes()
    },
    async addUnitType() {
      if (!this.unitForm.name) return
      await apiPost(API + "/unit-types", this.unitForm)
      this.unitForm = { name: "" }
      this.unitMsg = "添加成功"
      this.loadUnitTypes()
    },
    editUnitType(ut) {
      const newName = prompt("输入新名", ut.name)
      if (newName && newName !== ut.name) {
        apiPut(API + "/unit-types/" + ut.id, { name: newName }).then(() => this.loadUnitTypes())
      }
    },
    async deleteUnitType(id) {
      if (!confirm("确认删除?")) return
      await apiDelete(API + "/unit-types/" + id)
      this.loadUnitTypes()
    },
    async addEmployee() {
      if (!this.empForm.display_name || !this.empForm.username) return
      await apiPost(API + "/employees", this.empForm)
      this.empForm = { display_name: "", username: "", password: "" }
      this.empMsg = "添加成功"
      this.loadEmployees()
    },
    async deleteEmployee(id) {
      if (!confirm("确认删除?")) return
      await apiDelete(API + "/employees/" + id)
      this.loadEmployees()
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
      let total = 0
      for (const d of this.summaryData.details) {
        total += Number(this.getAlloc(d, userId))
      }
      return total
    },
    getColumnActualTotal(userId) {
      if (!this.summaryData || !this.summaryData.details) return 0
      let total = 0
      for (const d of this.summaryData.details) {
        const v = this.getActual(d, userId)
        total += (v === '-' ? 0 : Number(v))
      }
      return total
    },
    getGrandAllocTotal() {
      if (!this.summaryData || !this.summaryData.details) return 0
      let total = 0
      for (const d of this.summaryData.details) {
        total += this.getAllocTotal(d)
      }
      return total
    },
    getGrandActualTotal() {
      if (!this.summaryData || !this.summaryData.details) return 0
      return this.summaryData.details.reduce((s, d) => s + (d.total_actual ?? 0), 0)
    },
    downloadExcel() {
      if (!this.summaryData) return
      const table = document.getElementById("summary-table")
      if (!table) return
      let html = '<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">'
      html += '<head><meta charset="UTF-8"><!--[if gte mso 9]><xml><x:ExcelWorkbook><x:ExcelWorksheets><x:ExcelWorksheet><x:Name>全品类汇总</x:Name><x:WorksheetOptions><x:DisplayGridlines/></x:WorksheetOptions></x:ExcelWorksheet></x:ExcelWorksheets></x:ExcelWorkbook></xml><![endif]-->'
      html += '<style>th,td{border:1px solid #000;padding:4px 6px;font-size:12px;text-align:center}th{background:#d9e1f2;font-weight:700}td{vertical-align:middle}</style></head><body>'
      html += '<h2 style="text-align:center;font-size:16px;margin-bottom:8px">' + (this.summaryData.batch_name || "全品类汇总") + '</h2>'
      html += '<p style="text-align:center;font-size:12px;color:#666;margin-bottom:12px">到货时间: ' + (this.summaryData.arrival_time || "") + '</p>'
      html += table.outerHTML
      html += '</body></html>'
      const blob = new Blob([html], { type: "application/vnd.ms-excel" })
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = (this.summaryData.batch_name || "全品类汇总") + ".xls"
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    },
    logout() {
      localStorage.removeItem("user")
      this.$router.push("/login")
    },
    showItemDetail(item) {
      this.itemDetailView = item
    },
    backToBatchItems() {
      this.itemDetailView = null
    }
  }
}
</script>

<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f5f6fa; color: #333; }

.admin-layout { display: flex; height: 100vh; }
.sidebar { width: 220px; background: #1e2a3a; color: #ccc; display: flex; flex-direction: column; flex-shrink: 0; }
.sidebar-logo { padding: 20px; font-size: 18px; font-weight: bold; color: #fff; border-bottom: 1px solid #2a3a4a; display: flex; justify-content: space-between; align-items: center; }
.mobile-header { display: none; }
.hamburger { display: none; }
.item-name-cell { cursor: default; }
.sidebar-nav { flex: 1; padding: 12px 0; overflow-y: auto; }
.sidebar-nav a { display: block; padding: 10px 20px; color: #aaa; cursor: pointer; text-decoration: none; font-size: 14px; transition: 0.2s; }
.sidebar-nav a:hover { background: #2a3a4a; color: #fff; }
.sidebar-nav a.active { background: #3a4a5a; color: #fff; border-left: 3px solid #409eff; }
.sidebar-section-label { padding: 12px 20px 4px; font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: 1px; border-top: 1px solid #2a3a4a; margin-top: 8px; }
.sidebar-footer { padding: 16px 20px; border-top: 1px solid #2a3a4a; display: flex; justify-content: space-between; align-items: center; font-size: 13px; }

.main-content { flex: 1; padding: 24px; overflow-y: auto; }
.page-title { font-size: 22px; margin-bottom: 20px; }

.stats-row { display: flex; gap: 16px; margin-bottom: 24px; }
.stat-card { flex: 1; background: #fff; border-radius: 8px; padding: 20px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.stat-num { font-size: 32px; font-weight: bold; color: #409eff; }
.stat-label { font-size: 13px; color: #999; margin-top: 4px; }
.card { background: #fff; border-radius: 8px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 16px; }
.card h3 { margin-bottom: 12px; font-size: 16px; }

.data-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.data-table th, .data-table td { padding: 8px 10px; text-align: left; border-bottom: 1px solid #eee; }
.data-table th { background: #fafafa; font-weight: 600; color: #666; }
.data-table tr:hover { background: #f8f9fb; }

.batch-layout { display: flex; flex-direction: column; gap: 16px; }

.batch-right { flex: 1; background: #fff; border-radius: 8px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); overflow-x: auto; }
.batch-item { padding: 12px; border-radius: 6px; cursor: pointer; margin-bottom: 8px; border: 1px solid #eee; transition: 0.2s; }
.batch-item:hover { border-color: #409eff; }
.batch-item.active { border-color: #409eff; background: #ecf5ff; }
.batch-item-name { font-weight: 600; font-size: 15px; }
.batch-item-sub { font-size: 12px; color: #888; margin-top: 2px; }
.batch-item-meta { font-size: 11px; color: #aaa; margin-top: 2px; }
.batch-item-actions { margin-top: 6px; display: flex; gap: 6px; }

.empty-hint { text-align: center; color: #999; padding: 60px 20px; font-size: 15px; }

.btn { display: inline-block; padding: 6px 14px; border: 1px solid #dcdfe6; border-radius: 4px; background: #fff; cursor: pointer; font-size: 13px; transition: 0.2s; }
.btn:hover { border-color: #409eff; color: #409eff; }
.btn-primary { background: #409eff; border-color: #409eff; color: #fff; }
.btn-primary:hover { background: #66b1ff; border-color: #66b1ff; color: #fff; }
.btn-danger { background: #f56c6c; border-color: #f56c6c; color: #fff; }
.btn-danger:hover { background: #f78989; border-color: #f78989; color: #fff; }
.btn-sm { padding: 4px 10px; font-size: 12px; }
.btn-xs { padding: 2px 8px; font-size: 11px; }

.status-badge { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px; }
.status-pending { background: #fdf6ec; color: #e6a23c; }
.status-warn { background: #fef0f0; color: #f56c6c; }
.status-ok { background: #f0f9eb; color: #67c23a; }

.modal-mask { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal-card { background: #fff; border-radius: 10px; padding: 24px; width: 480px; max-width: 90vw; max-height: 80vh; overflow-y: auto; box-shadow: 0 8px 30px rgba(0,0,0,0.15); }
.modal-card h3 { margin-bottom: 16px; font-size: 18px; }
.modal-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 16px; }

.form-group { margin-bottom: 12px; }
.form-group label { display: block; font-size: 13px; color: #666; margin-bottom: 4px; }
.form-group input, .form-group select { width: 100%; padding: 8px 10px; border: 1px solid #dcdfe6; border-radius: 4px; font-size: 14px; outline: none; }
.form-group input:focus, .form-group select:focus { border-color: #409eff; }

@media print { .no-print { display: none !important; } }
#print-zone h3 { margin-bottom: 8px; }
#print-zone p { color: #888; margin-bottom: 12px; font-size: 14px; }

::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-thumb { background: #ccc; border-radius: 3px; }
::-webkit-scrollbar-track { background: transparent; }

/* ===== 矩阵表格样式 ===== */
.batch-select-bar {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  margin-bottom: 16px;
}
.batch-select {
  flex: 1;
  max-width: 500px;
  padding: 8px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 14px;
  outline: none;
  background: #fff;
}
.batch-select:focus { border-color: #409eff; }

/* 矩阵表格 - 首列固定 */
.matrix-table-wrap {
  overflow-x: auto;
  margin-top: 4px;
  position: relative;
}
.matrix-table {
  border-collapse: separate;
  border-spacing: 0;
}
.matrix-table th.col-name,
.matrix-table td:first-child {
  position: sticky;
  left: 0;
  z-index: 2;
  background: #fff;
  border-right: 2px solid #e8e8e8;
}
.matrix-table thead th.col-name {
  z-index: 3;
  background: #f5f7fa;
}
.matrix-table tfoot td:first-child {
  background: #fafbfc;
}
.matrix-table tbody tr:hover td:first-child {
  background: #f0f7ff;
}
.batch-select-bar {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  margin-bottom: 16px;
}
.batch-select {
  flex: 1;
  max-width: 500px;
  padding: 8px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 14px;
  outline: none;
  background: #fff;
}
.batch-select:focus { border-color: #409eff; }

/* 矩阵表格 - 首列固定 */
.matrix-table-wrap {
  overflow-x: auto;
  margin-top: 4px;
  position: relative;
}
.matrix-table {
  border-collapse: separate;
  border-spacing: 0;
}
.matrix-table th.col-name,
.matrix-table td:first-child {
  position: sticky;
  left: 0;
  z-index: 2;
  background: #fff;
  border-right: 2px solid #e8e8e8;
}
.matrix-table thead th.col-name {
  z-index: 3;
  background: #f5f7fa;
}
.matrix-table tfoot td:first-child {
  background: #fafbfc;
}
.matrix-table tbody tr:hover td:first-child {
  background: #f0f7ff;
}

.matrix-table { width: 100%; border-collapse: collapse; font-size: 13px; min-width: 500px; }
.matrix-table th, .matrix-table td { padding: 3px 3px; text-align: center; white-space: nowrap; border: 1px solid #000; }
.matrix-table th { background: #d9e1f2; font-weight: 700; color: #333; font-size: 12px; }
.matrix-table thead th { border-bottom: 2px solid #000; }
.matrix-table tbody tr:nth-child(even) { background: #f8f9fc; }
.matrix-table tfoot td { background: #eef1f8; font-weight: 600; border-top: 2px solid #000; }
.matrix-table tbody tr:hover { background: #eef2fa; }
.matrix-table .col-name { text-align: left; min-width: 65px; }
.matrix-table .col-unit { min-width: 32px; }
.matrix-table .col-emp { min-width: 55px; background: #ecf5ff; color: #409eff; font-weight: 600; padding: 2px 2px !important; font-size: 11px; }
.emp-header-name { font-size: 11px; }
.emp-header-sub { font-size: 9px; font-weight: 400; color: #99c9ff; margin-top: 1px; }
.matrix-table .col-total { min-width: 35px; background: #fdf6ec; color: #e6a23c; font-weight: 600; }
.matrix-table .col-status { min-width: 30px; }
.matrix-table .col-remark { min-width: 50px; font-size: 11px; color: #909399; }
.matrix-table .cell-remark { max-width: 55px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 11px; color: #666; }
.cell-input { width: 36px; padding: 2px 1px; border: 1px solid #dcdfe6; border-radius: 2px; font-size: 12px; text-align: center; outline: none; background: #fff; }
.cell-qty { padding: 2px 2px !important; vertical-align: top; }
.cell-qty-row { margin-bottom: 1px; }
.cell-qty-alloc { padding: 1px 1px !important; vertical-align: top; }
.cell-qty-actual { padding: 1px 2px !important; vertical-align: top; min-width: 28px; }
.cell-actual-row { padding-top: 1px; border-top: 1px dashed #ddd; }
.actual-qty { font-size: 11px; color: #67c23a; font-weight: 600; }
.actual-qty::before { font-size: 9px; color: #999; margin-right: 1px; }
.cell-input:focus { border-color: #409eff; box-shadow: 0 0 0 2px rgba(64,158,255,0.2); }
.cell-input:hover { border-color: #c0c4cc; }
/* Hide spin buttons */
.cell-input[type=number] { -moz-appearance: textfield; }
.cell-input::-webkit-inner-spin-button,
.cell-input::-webkit-outer-spin-button { -webkit-appearance: none; margin: 0; }
.matrix-table .col-actions { min-width: 50px; width: 50px; }
.matrix-table .cell-qty-alloc { font-weight: 500; color: #303133; }
.matrix-table .cell-qty-actual { font-weight: 500; color: #67c23a; }
.matrix-table .cell-total { font-weight: 600; color: #e6a23c; }
.matrix-table .cell-total-actual { font-weight: 600; color: #67c23a; }
.action-group { display: flex; gap: 4px; justify-content: center; }

/* ===== 响应式布局 - 手机端===== */
/* ===== 全品类汇总- 矩阵样式 ===== */
.summary-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.summary-table th, .summary-table td { border: 1px solid #000; padding: 2px 3px; text-align: center; font-size: 12px; }
.summary-table thead th { background: #d9e1f2; font-weight: 700; color: #333; font-size: 11px; border-bottom: 2px solid #000; }
.summary-table tbody tr:nth-child(even) { background: #f8f9fc; }
.summary-table tfoot td { background: #eef1f8; font-weight: 600; border-top: 2px solid #000; }
.sum-col-idx { width: 35px; }
.sum-col-name { text-align: left; min-width: 60px; width: 60px; }
.sum-col-unit { width: 35px; }
.sum-col-emp { min-width: 42px; background: #ecf5ff; padding: 2px 2px !important; font-size: 11px; }
.sum-col-total { min-width: 38px; background: #fdf6ec; font-weight: 600; font-size: 11px; }
.sum-emp-name { font-size: 11px; color: #409eff; }
.sum-emp-sub { font-size: 9px; color: #99c9ff; display: flex; justify-content: center; gap: 1px; margin-top: 1px; }
.sum-sub-alloc { color: #e6a23c; }
.sum-sub-div { color: #ccc; }
.sum-sub-actual { color: #67c23a; }
.sum-name { text-align: left; font-weight: 500; }
.sum-idx { color: #909399; font-size: 12px; }
.sum-unit { font-size: 12px; color: #606266; }
.sum-cell { font-size: 13px; padding: 6px 4px !important; }
.sum-cell-alloc { color: #e6a23c; font-weight: 500; }
.sum-cell-actual { color: #67c23a; font-weight: 500; }
.sum-total { font-weight: 600; font-size: 13px; }
.sum-total-alloc { color: #e6a23c; background: #fdf6ec; }
.sum-total-actual { color: #67c23a; background: #f0f9eb; }

@media print {
  .no-print { display: none !important; }
  .summary-table { font-size: 11px; }
  .summary-table th, .summary-table td { border-color: #000; padding: 1px 2px; }
}

@media (max-width: 768px) {
  /* 侧边栏*/
  .sidebar { position: fixed; z-index: 1000; height: 100vh; transform: translateX(-100%); transition: transform 0.25s ease; }
  .sidebar.open { transform: translateX(0); box-shadow: 4px 0 20px rgba(0,0,0,0.3); }
  .sidebar-logo { display: flex; justify-content: space-between; align-items: center; }
  .hamburger { display: inline-block; background: none; border: none; color: #fff; font-size: 22px; cursor: pointer; padding: 0 4px; line-height: 1; }
  .admin-layout { flex-direction: column; }
  .main-content { padding: 12px; margin-left: 0; }
  .mobile-header { display: flex; position: relative; align-items: center; gap: 10px; padding: 8px 0 12px; border-bottom: 1px solid #eee; margin-bottom: 12px; }
  .mobile-header .hamburger { position: fixed; top: 10px; left: 10px; z-index: 1001; width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; background: rgba(255,255,255,0.95); border-radius: 6px; box-shadow: 0 2px 8px rgba(0,0,0,0.12); color: #333; font-size: 22px; }
  .mobile-title { font-size: 16px; font-weight: 600; color: #303133; padding-left: 44px; }

  /* 批次选择栏*/
  .batch-select-bar { flex-wrap: wrap; gap: 8px; padding: 10px 12px; }
  .batch-select-bar select { flex: 1; min-width: 120px; max-width: none; }

  /* 矩阵表格 - 手机端端用卡片替代 */
  .matrix-table-wrap { overflow-x: auto; }
  .matrix-table { font-size: 12px; min-width: 400px; border: 1px solid #000; }
  .matrix-table th, .matrix-table td { padding: 2px 2px; border-color: #000; }
  .matrix-table .col-name { min-width: 70px; }
  .matrix-table .col-emp { min-width: 50px; font-size: 11px; }
  .item-name-cell { cursor: pointer; color: #409eff; text-decoration: underline; }

  /* 基础信息表单 */
  .card .form-inline, .card > div[style*="flex"] { flex-direction: column; align-items: stretch; }
  .card input { max-width: none !important; width: 100% !important; }

  /* 统计卡片 */
  .stats-row { flex-wrap: wrap; }
  .stat-card { min-width: calc(50% - 8px); }

  /* 分单批次列表 - 卡片布局 */
  .batch-list-page .data-table,
  .batch-list-page .data-table thead,
  .batch-list-page .data-table tbody,
  .batch-list-page .data-table tr,
  .batch-list-page .data-table th,
  .batch-list-page .data-table td {
    display: block;
  }
  .batch-list-page .data-table thead { display: none; }
  .batch-list-page .data-table tr {
    background: #fff;
    border-radius: 10px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    padding: 14px 16px;
    margin-bottom: 12px;
    border: 1px solid #eee;
  }
  .batch-list-page .data-table td {
    border: none;
    padding: 4px 0;
    font-size: 13px;
    text-align: left;
  }
  .batch-list-page .data-table td:first-child {
    font-size: 16px;
    font-weight: 600;
    padding-bottom: 6px;
    color: #303133;
  }
  .batch-list-page .data-table td:nth-child(2)::before { content: "到货时间: "; color: #909399; font-size: 12px; }
  .batch-list-page .data-table td:nth-child(3)::before { content: "货品数: "; color: #909399; font-size: 12px; }
  .batch-list-page .data-table td:nth-child(4)::before { content: "备注: "; color: #909399; font-size: 12px; }
  .batch-list-page .data-table td:nth-child(5)::before { content: "创建: "; color: #909399; font-size: 12px; }
  .batch-list-page .data-table td:last-child {
    padding-top: 10px;
    margin-top: 8px;
    border-top: 1px solid #f0f0f0;
    width: auto;
  }
  .batch-list-page .data-table .cell-remark { max-width: none; }

  /* 弹窗 */
  .modal-card { width: 95vw; padding: 16px; }
  .modal-card-wide { width: 95vw; padding: 16px; }

  /* 全品类汇总*/
  #print-zone .data-table { font-size: 12px; }
  #print-zone .data-table th, #print-zone .data-table td { padding: 4px; }

  /* 移动端分配列表*/
  .mobile-assign-list .cell-input { width: 60px; }
}

/* ===== 分单批次列表样式 ===== */
.batch-list-page .data-table td { vertical-align: middle; }
.batch-list-page .data-table .cell-remark { max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #909399; font-size: 12px; }
</style>








