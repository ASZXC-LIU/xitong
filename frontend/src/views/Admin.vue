<template>
  <div class="admin-layout">
    <aside class="sidebar" :class="{ open: sidebarOpen }" @click.self="sidebarOpen = false">
      <div class="sidebar-logo">
        <span>分单系统</span>
        <button class="hamburger" @click.stop="sidebarOpen = !sidebarOpen">{{ sidebarOpen ? "✕" : "☰" }}</button>
      </div>
      <nav class="sidebar-nav" @click.stop>
        <a :class="{ active: currentPage === 'dashboard' }" @click="goToDashboard">首页概览</a>
        <a :class="{ active: currentPage === 'batches' }" @click="goToBatches">分单管理</a>
        <a :class="{ active: currentPage === 'batchList' }" @click="currentPage = 'batchList'; loadBatches()">分单批次</a>
        <div class="sidebar-section-label">基础信息</div>
        <a :class="{ active: currentPage === 'cargoTypes' }" @click="currentPage = 'cargoTypes'">货品种类</a>
        <a :class="{ active: currentPage === 'employeeMgmt' }" @click="currentPage = 'employeeMgmt'">人员管理</a>
        <a :class="{ active: currentPage === 'unitTypes' }" @click="currentPage = 'unitTypes'">单位管理</a>
        <a :class="{ active: currentPage === 'summary' }" @click="openSummary">全品类汇总</a>
      </nav>
      <div class="sidebar-footer" @click.stop>
        <span>{{ user.display_name }}</span>
        <button class="btn btn-sm btn-danger" @click="logout">退</button>
      </div>
    </aside>

    <main class="main-content" @click="sidebarOpen = false">
      <div class="mobile-header">
        <button class="hamburger" @click.stop="sidebarOpen = !sidebarOpen">{{ sidebarOpen ? "✕" : "☰" }}</button>
        <span class="mobile-title">{{ mobilePageTitle }}</span>
      </div>

      <div v-if="currentPage === 'dashboard'">
        <h2 class="page-title">首页概览</h2>
        <div class="stats-row">
          <div class="stat-card">
            <div class="stat-num">{{ stats.totalBatches }}</div>
            <div class="stat-label">总批</div>
          </div>
          <div class="stat-card">
            <div class="stat-num">{{ stats.totalItems }}</div>
            <div class="stat-label">最新货</div>
            <div
              style="font-size:11px;color:#909399;margin-top:2px;max-width:140px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
              :title="stats.latestBatchName">{{ stats.latestBatchName }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-num" style="color:#e6a23c">{{ stats.pendingItems }}</div>
            <div class="stat-label">待报</div>
            <div
              style="font-size:11px;color:#909399;margin-top:2px;max-width:140px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
              :title="stats.latestBatchName">{{ stats.latestBatchName }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-num" style="color:#67c23a">{{ stats.doneItems }}</div>
            <div class="stat-label">已完</div>
            <div
              style="font-size:11px;color:#909399;margin-top:2px;max-width:140px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
              :title="stats.latestBatchName">{{ stats.latestBatchName }}</div>
          </div>
        </div>
        <div class="card">
          <table v-if="batches.length">
            <thead>
              <tr>
                <th>批次名称</th>
                <th>到货时间</th>
                <th>货品</th>
                <th>创建时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="b in batches.slice(0, 10)" :key="b.id">
                <td>{{ b.name }}</td>
                <td>{{ b.arrival_time }}</td>
                <td>{{ b.item_count }}</td>
                <td>{{ b.created_at }}</td>
              </tr>
            </tbody>
          </table>
          <p v-else style="color:#999;text-align:center;padding:20px">暂无批次</p>
        </div>
      </div>

      <div v-if="currentPage === 'batches'">
        <h2 class="page-title">分单管理</h2>
        <div class="batch-layout">
          <div class="batch-select-bar">
            <label style="font-weight:600;margin-right:8px;white-space:nowrap">选择批次:</label>
            <select v-model="selectedBatchId" @change="onBatchSelectChange" class="batch-select">
              <option value="" disabled>-- 请选择批次 --</option>
              <option v-for="b in sortedBatches" :key="b.id" :value="b.id">
                {{ b.name }} ({{ b.status }} | 到货: {{ b.arrival_time }} | {{ b.item_count }} 个货)
              </option>
            </select>
            <button class="btn btn-sm btn-primary" @click="showBatchFormForCreate" style="margin-left:10px">+ 新建</button>
            <button class="btn btn-sm" @click="openReportForSelected" style="margin-left:6px"
              :disabled="!selectedBatchId">明细</button>
            <button class="btn btn-sm btn-danger" @click="deleteBatch(selectedBatch)" style="margin-left:6px"
              :disabled="!selectedBatch || !selectedBatch.can_delete"
              :title="selectedBatch?.can_delete ? '删除空批次' : '已有分货或报货记录的批次只能关闭'">删除</button>
            <button v-if="selectedBatch && selectedBatch.status === '已完成'" class="btn btn-sm btn-danger" @click="closeBatch(selectedBatch)" style="margin-left:6px">关闭批次</button>
            <button v-if="selectedBatch && selectedBatch.status === '已关闭'" class="btn btn-sm" @click="reopenBatch(selectedBatch)" style="margin-left:6px">重新打开</button>
          </div>

          <div class="batch-right">
            <div v-if="!selectedBatchId" class="empty-hint">请选择一个批次</div>
            <template v-else>
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
                <div style="display:flex;align-items:center;gap:8px">
                  <strong>货品列表</strong>
                  <span :class="['status-badge', batchStatusClass(selectedBatch?.status)]">{{ selectedBatch?.status }}</span>
                </div>
                <div>
                  <button class="btn btn-primary" @click="saveAllAssignments" :disabled="hasAllocationErrors || selectedBatch?.status === '已关闭'">保存分货</button>
                </div>
              </div>
              <div class="matrix-filters">
                <label>产品搜索<input v-model.trim="itemSearch" type="search" placeholder="输入产品简称" /></label>
                <label>状态筛选
                  <select v-model="itemStatusFilter">
                    <option value="all">全部</option>
                    <option value="over">分货超量</option>
                    <option value="pending">待报货</option>
                    <option value="done">已完成</option>
                    <option value="unallocated">未分货</option>
                  </select>
                </label>
              </div>
              <div v-if="items.length === 0" class="empty-hint">暂无货品</div>
              <div v-else-if="filteredItems.length === 0" class="empty-hint">没有符合条件的产品</div>
              <div v-else class="matrix-table-wrap">
                <table class="matrix-table">
                  <thead>
                    <tr>
                      <th class="col-name">货品名称</th>
                      <th class="col-total">公司到货</th>
                      <th v-for="emp in matrixEmployees" :key="emp.id" class="col-emp" colspan="2">
                        <div class="emp-header-name">{{ emp.name }}</div>
                        <div class="emp-header-sub"><span class="sum-sub-alloc col-type-alloc">分货</span><span
                            class="sum-sub-div">/</span><span class="sum-sub-actual col-type-actual">报货</span></div>
                      </th>
                      <th class="col-total col-type-alloc">总分货</th>
                      <th class="col-total col-type-actual">总报货</th>
                      <th class="col-total">剩余</th>
                      <th class="col-status">状态</th>
                      <th class="col-remark">备注</th>
                      <th class="col-actions">操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="item in filteredItems" :key="item.id" :class="{ 'allocation-error-row': getItemRemaining(item) < 0 || !isCompanyQuantityValid(item) }">
                      <td class="item-name-cell">
                        <input v-if="item.isTemp" type="text" v-model="item.name" placeholder="货品名称" class="name-input" />
                        <strong v-else @click="showItemDetail(item)">{{ item.name }}</strong>
                      </td>
                      <td class="cell-qty-alloc">
                        <input type="text" v-model="item.company_quantity" inputmode="decimal" class="cell-input" aria-label="公司到货量" />
                      </td>
                      <template v-for="emp in matrixEmployees" :key="emp.id">
                        <td class="cell-qty-alloc col-type-alloc">
                          <input type="text" :value="getItemQty(item, emp.id)"
                            @input="updateLocalData(item, emp.id, $event.target.value)"
                            @focus="$event.target.select()"
                            @keyup.enter="$event.target.blur()"
                            :disabled="selectedBatch?.status === '已关闭'"
                            class="cell-input" />
                        </td>
                        <td class="cell-qty-actual col-type-actual">
                          <span class="actual-qty">{{ getItemActual(item, emp.id) }}</span>
                          <span v-if="getOriginalActual(item, emp.id) !== '-'" class="original-actual">原报 {{ getOriginalActual(item, emp.id) }}</span>
                          <button v-if="isAssignmentLocked(item, emp.id) && selectedBatch?.status !== '已关闭'"
                            class="btn btn-xs unlock-button" @click="unlockAssignment(item, getAssignment(item, emp.id))">解锁</button>
                        </td>
                      </template>
                      <td class="cell-total col-type-alloc">{{ getItemTotal(item) }}</td>
                      <td class="cell-total cell-total-actual col-type-actual">{{ getItemActualTotal(item) }}</td>
                      <td class="cell-total" :class="{ 'quantity-error': getItemRemaining(item) < 0 }">{{ getItemRemaining(item) }}</td>
                      <td><span
                          :class="'status-badge ' + (item.status === '未分货' ? 'status-pending' : item.status === '待报货' ? 'status-warn' : 'status-ok')">{{
                          item.status }}</span></td>
                      <td class="cell-remark">{{ item.remark || '无备注' }}</td>
                      <td>
                        <div class="action-group">
                        <button class="btn btn-xs" @click="showItemDetail(item)">分货</button>
                        <button class="btn btn-xs btn-primary" @click="startEdit(item)" style="margin-right: 4px;">修改</button>
                          <button class="btn btn-xs btn-danger" @click="deleteItem(item)" title="删除此货物">删除</button>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                  <tfoot v-if="items.length > 1">
                    <tr>
                      <td><strong>合计</strong></td>
                      <td class="cell-total">{{ getCompanyGrandTotal() }}</td>
                      <template v-for="emp in matrixEmployees" :key="emp.id">
                        <td class="cell-total col-type-alloc">{{ getColumnTotal(emp.id) }}</td>
                        <td class="cell-total cell-total-actual col-type-actual">{{ getMatrixColumnActualTotal(emp.id) }}</td>
                      </template>
                      <td class="cell-total col-type-alloc">{{ getGrandTotal() }}</td>
                      <td class="cell-total cell-total-actual col-type-actual">{{ getMatrixGrandActualTotal() }}</td>
                      <td class="cell-total">{{ getRemainingGrandTotal() }}</td>
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

      <div v-if="currentPage === 'cargoTypes'">
        <h2 class="page-title">货品种类管理</h2>
        <div class="card">
          <div class="master-form">
            <input v-model="cargoForm.name" placeholder="种类名称" style="max-width:200px" />
            <input v-model="cargoForm.default_unit" list="default-unit-list" placeholder="默认单位" style="max-width:200px"
              autocomplete="off" />
            <datalist id="default-unit-list">
              <option v-for="ut in activeUnitTypes" :key="ut.id" :value="ut.name">{{ ut.name }}</option>
            </datalist>
            <button class="btn btn-primary btn-sm" @click="addCargoType">添加</button>
          </div>
          <p v-if="cargoMsg" :class="['form-message', { 'is-error': cargoMsgError }]">{{ cargoMsg }}</p>
          <div class="master-table-wrap"><table class="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>种类名称</th>
                <th>默认单位</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="ct in cargoTypes" :key="ct.id">
                <td>{{ ct.id }}</td>
                <td>{{ ct.name }}</td>
                <td>{{ ct.default_unit }}</td>
                <td><span :class="['status-badge', ct.is_active ? 'is-active' : 'is-inactive']">{{ ct.is_active ? '启用' : '停用' }}</span></td>
                <td class="action-cell">
                  <button class="btn btn-sm" @click="editCargoType(ct)">编辑</button>
                  <button :class="['btn','btn-sm', ct.is_active ? 'btn-danger' : 'btn-status']" @click="toggleCargoType(ct)">{{ ct.is_active ? '停用' : '启用' }}</button>
                </td>
              </tr>
            </tbody>
          </table></div>
        </div>

        <div v-if="showCargoEditModal" class="modal-mask" @click.self="showCargoEditModal=false">
          <div class="modal-card master-edit-modal">
            <h3>编辑产品</h3>
            <div class="form-group"><label>产品名称</label><input v-model="cargoEditForm.name" /></div>
            <div class="form-group"><label>默认单位</label><input v-model="cargoEditForm.default_unit" list="default-unit-list" /></div>
            <p v-if="cargoEditMsg" class="form-error">{{ cargoEditMsg }}</p>
            <div class="modal-actions"><button class="btn" @click="showCargoEditModal=false">取消</button><button class="btn btn-primary" @click="saveCargoEdit">保存修改</button></div>
          </div>
        </div>
      </div>

      <div v-if="currentPage==='employeeMgmt'">
        <h2 class="page-title">人员管理</h2>
        <div class="card">
          <div class="master-form">
            <input v-model="empForm.display_name" placeholder="员工姓名" style="max-width:150px" />
            <input v-model="empForm.phone" inputmode="numeric" maxlength="11" placeholder="员工手机号" style="max-width:180px" />
            <button class="btn btn-primary btn-sm" @click="addEmployee">添加</button>
          </div>
          <p v-if="empMsg" :class="['form-message', { 'is-error': empMsgError }]">{{ empMsg }}</p>
          <div class="master-table-wrap"><table class="data-table">
            <thead><tr><th>ID</th><th>姓名</th><th>手机号</th><th>角色</th><th>状态</th><th>操作</th></tr></thead>
            <tbody>
              <tr v-for="e in employees" :key="e.id">
                <td>{{ e.id }}</td><td>{{ e.display_name }}</td><td>{{ e.phone || e.username }}</td>
                <td><span :style="e.role === 'admin' ? 'color:#e6a23c;font-weight:bold;' : ''">{{ e.role === 'admin' ? '管理员' : '员工' }}</span></td>
                <td><span :class="['status-badge', e.is_active ? 'is-active' : 'is-inactive']">{{ e.is_active ? '启用' : '停用' }}</span></td>
                <td class="action-cell">
                  <button v-if="e.role !== 'admin'" class="btn btn-sm" @click="editEmployee(e)">编辑</button>
                  <button v-if="e.role !== 'admin'" :class="['btn','btn-sm', e.is_active ? 'btn-danger' : 'btn-status']" @click="toggleEmployee(e)">{{ e.is_active ? '停用' : '启用' }}</button>
                </td>
              </tr>
            </tbody>
          </table></div>
        </div>

        <div v-if="showEmpEditModal" class="modal-mask" @click.self="showEmpEditModal=false">
          <div class="modal-card" style="width: 350px;">
            <h3>编辑信息</h3>
            <div class="form-group">
              <label>姓名</label>
              <input v-model="empEditForm.display_name" placeholder="姓名" />
            </div>
            <div class="form-group">
              <label>员工手机号</label>
              <input v-model="empEditForm.phone" inputmode="numeric" maxlength="11" placeholder="11位手机号" />
            </div>
            <div class="modal-actions">
              <button class="btn" @click="showEmpEditModal=false">取消</button>
              <button class="btn btn-primary" @click="saveEmployeeEdit">保存修改</button>
            </div>
            <p v-if="empEditMsg" style="color:#f56c6c; margin-top: 10px; font-size: 13px;">{{ empEditMsg }}</p>
          </div>
        </div>
      </div>

      <div v-if="currentPage === 'unitTypes'">
        <h2 class="page-title">单位管理</h2>
        <div class="card">
          <div class="master-form">
            <input v-model="unitForm.name" placeholder="单位名称" style="max-width:200px" />
            <button class="btn btn-primary btn-sm" @click="addUnitType">添加</button>
          </div>
          <p v-if="unitMsg" :class="['form-message', { 'is-error': unitMsgError }]">{{ unitMsg }}</p>
          <div class="master-table-wrap"><table class="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>单位名称</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="ut in unitTypes" :key="ut.id">
                <td>{{ ut.id }}</td>
                <td>{{ ut.name }}</td>
                <td><span :class="['status-badge', ut.is_active ? 'is-active' : 'is-inactive']">{{ ut.is_active ? '启用' : '停用' }}</span></td>
                <td class="action-cell">
                  <button class="btn btn-sm" @click="editUnitType(ut)">编辑</button>
                  <button :class="['btn','btn-sm', ut.is_active ? 'btn-danger' : 'btn-status']" @click="toggleUnitType(ut)">{{ ut.is_active ? '停用' : '启用' }}</button>
                </td>
              </tr>
            </tbody>
          </table></div>
        </div>

        <div v-if="showUnitEditModal" class="modal-mask" @click.self="showUnitEditModal=false">
          <div class="modal-card master-edit-modal">
            <h3>编辑单位</h3>
            <div class="form-group"><label>单位名称</label><input v-model="unitEditForm.name" /></div>
            <p v-if="unitEditMsg" class="form-error">{{ unitEditMsg }}</p>
            <div class="modal-actions"><button class="btn" @click="showUnitEditModal=false">取消</button><button class="btn btn-primary" @click="saveUnitEdit">保存修改</button></div>
          </div>
        </div>
      </div>

      <div v-if="currentPage === 'summary'">
        <h2 class="page-title">全品类汇总</h2>
        <div class="card no-print" style="display:flex;gap:8px;align-items:center;margin-bottom:16px;flex-wrap:wrap">
          <div style="display:flex;align-items:center;gap:8px;flex:1;min-width:200px">
            <label style="font-weight:600;white-space:nowrap;font-size:14px">选择批次:</label>
            <select v-model="summaryBatchId" @change="onSummaryBatchChange" class="batch-select"
              style="max-width:300px">
              <option value="">-- 请选择批次 --</option>
              <option v-for="b in sortedBatches" :key="b.id" :value="b.id">
                {{ b.name }} ({{ b.arrival_time }})
              </option>
            </select>
          </div>
          <button class="btn btn-primary btn-sm" @click="printPage" :disabled="!summaryData">打印</button>
          <button class="btn btn-sm" @click="downloadExcel" :disabled="!summaryData"
            style="background:#67c23a;color:#fff;border-color:#67c23a">下载Excel</button>
        </div>
        <div v-if="!summaryData" style="text-align:center;color:#999;padding:60px 20px;font-size:15px">
          请从分单批次或分单管理中选择一个批次查看汇总
        </div>
        <div v-else id="print-zone">
          <table class="summary-table" id="summary-table">
            <thead>
              <tr>
                <th class="sum-col-idx">序号</th>
                <th class="sum-col-name">货品名称</th>
                <th class="sum-col-total">公司到货</th>
                <th v-for="emp in summaryEmployees" :key="emp.id" class="sum-col-emp" colspan="2">
                  <div class="sum-emp-name">{{ emp.name }}</div>
                  <div class="sum-emp-sub">
                    <span class="sum-sub-alloc col-type-alloc">分货</span>
                    <span class="sum-sub-div">/</span>
                    <span class="sum-sub-actual col-type-actual">报货</span>
                  </div>
                </th>
                <th class="sum-col-total">总分货</th>
                <th class="sum-col-total">总报货</th>
                <th class="sum-col-total">剩余</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(d, idx) in summaryData.details" :key="d.item_name">
                <td class="sum-idx">{{ idx + 1 }}</td>
                <td class="sum-name">{{ d.item_name }}</td>
                <td class="sum-total">{{ d.company_quantity }}</td>
                <template v-for="emp in summaryEmployees" :key="emp.id">
                  <td class="sum-cell sum-cell-alloc">{{ getAlloc(d, emp.id) }}</td>
                  <td class="sum-cell sum-cell-actual">{{ getActual(d, emp.id) }}</td>
                </template>
                <td class="sum-total sum-total-alloc">{{ d.total_allocated }}</td>
                <td class="sum-total sum-total-actual">{{ d.total_actual ?? '-' }}</td>
                <td class="sum-total">{{ d.remaining_quantity }}</td>
              </tr>
            </tbody>
            <tfoot>
              <tr>
                <td></td>
                <td style="text-align:center;font-weight:600;padding:8px 10px">合计</td>
                <td class="sum-total">{{ summaryData.totals.company_quantity }}</td>
                <template v-for="emp in summaryEmployees" :key="emp.id">
                  <td class="sum-total sum-total-alloc">{{ emp.allocated_quantity }}</td>
                  <td class="sum-total sum-total-actual">{{ emp.actual_quantity }}</td>
                </template>
                <td class="sum-total sum-total-alloc">{{ summaryData.totals.allocated_quantity }}</td>
                <td class="sum-total sum-total-actual">{{ summaryData.totals.actual_quantity }}</td>
                <td class="sum-total">{{ summaryData.totals.remaining_quantity }}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      <div v-if="currentPage === 'batchList'" class="batch-list-page">
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
                <th>状态</th>
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
                <td><span :class="['status-badge', batchStatusClass(b.status)]">{{ b.status }}</span></td>
                <td class="cell-remark">{{ b.batch_remark || '无备注' }}</td>
                <td>{{ b.created_at?.slice(0, 16) }}</td>
                <td>
                  <div class="action-group" style="display:flex;gap:4px;flex-wrap:wrap">
                    <button class="btn btn-xs btn-primary" @click="goToBatchManagement(b)">分单</button>
                    <button class="btn btn-xs" @click="editBatch(b)">编辑</button>
                    <button v-if="b.status === '已完成'" class="btn btn-xs btn-danger" @click="closeBatch(b)">关闭</button>
                    <button v-if="b.status === '已关闭'" class="btn btn-xs" @click="reopenBatch(b)">重新打开</button>
                    <button class="btn btn-xs btn-danger" @click="deleteBatch(b)" :disabled="!b.can_delete"
                      :title="b.can_delete ? '删除空批次' : '已有分货或报货记录的批次只能关闭'">删除</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
          <p v-else style="text-align:center;color:#999;padding:40px">暂无批次</p>
        </div>
      </div>
    </main>

    <div v-if="showBatchForm" class="modal-mask" @click.self="closeBatchForm">
      <div class="modal-card" :style="{ width: parsedExcelData.length ? '80vw' : '480px', maxWidth: '1000px' }">
        <h3>{{ editingBatchId ? '编辑批次' : '新建报货批次' }}</h3>
        
        <div style="display:flex; gap:16px; flex-wrap:wrap;">
          <div style="flex:1; min-width:200px;">
            <div class="form-group">
              <label>正式批次名称 <span style="color:red">*</span></label>
              <input v-model="batchForm.name" placeholder="请确认正式批次名称" />
            </div>
            <div class="form-group">
              <label>到货日期 <span style="color:red">*</span></label>
              <input type="date" v-model="batchForm.arrival_time" />
            </div>
            <div class="form-group">
              <label>批号备注</label>
              <input v-model="batchForm.batch_remark" placeholder="备注信息（可选）" />
            </div>
            
            <div v-if="!editingBatchId" class="form-group" style="margin-top:20px; padding-top:16px; border-top:1px dashed #ddd;">
              <label style="color:#409eff; font-weight:bold;">Excel 导入（优先）</label>
              <p style="font-size:12px; color:#667085; margin-bottom:8px;">仅读取“原始导入表”的 A1 批次参考名称、A 列产品简称和 B 列曲周到货量；不会匹配员工或产品资料库。</p>
              <input type="file" accept=".xlsx, .xls" @change="handleFileUpload" style="padding: 4px;" />
              <p v-if="importErrors.length" class="form-error">发现 {{ importErrors.length }} 处 Excel 错误，请逐项修正后重新选择文件。</p>
              <table v-if="importErrors.length" class="data-table" style="font-size:12px;margin-top:8px">
                <thead><tr><th>工作表</th><th>单元格</th><th>原值</th><th>原因</th></tr></thead>
                <tbody><tr v-for="(error, index) in importErrors" :key="index"><td>{{ error.sheet || '-' }}</td><td>{{ error.cell || '-' }}</td><td>{{ error.value || '-' }}</td><td>{{ error.reason }}</td></tr></tbody>
              </table>

              <template v-if="!importFile && !importErrors.length">
                <p style="font-size:12px;color:#667085;margin:12px 0 6px">不导入时，请从产品资料库选择产品并填写每项公司到货量。</p>
                <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
                  <select v-model="selectedCargoTypeId" style="min-width:200px"><option value="">选择产品</option><option v-for="cargo in cargoTypes.filter(c => c.is_active)" :key="cargo.id" :value="String(cargo.id)">{{ cargo.name }}{{ cargo.default_unit ? '（' + cargo.default_unit + '）' : '' }}</option></select>
                  <button type="button" class="btn btn-sm" @click="addManualItem">加入产品</button>
                </div>
                <div v-for="(item, index) in manualItems" :key="item.cargo_type_id" style="display:flex;gap:8px;margin-top:8px;align-items:center">
                  <span style="flex:1">{{ item.name }}{{ item.unit ? '（' + item.unit + '）' : '' }}</span>
                  <input v-model="item.company_quantity" inputmode="decimal" placeholder="公司到货量" style="width:120px" />
                  <button type="button" class="btn btn-xs btn-danger" @click="manualItems.splice(index, 1)">移除</button>
                </div>
              </template>
            </div>
          </div>

          <div v-if="parsedExcelData.length > 0 && !editingBatchId" style="flex: 2; border-left: 1px solid #eee; padding-left:16px; max-height: 400px; overflow-y:auto;">
            <h4 style="margin-bottom: 8px; color: #67c23a;">数据预览 (共 {{ parsedExcelData.length }} 条)</h4>
           <table class="data-table" style="font-size:12px;">
              <thead>
                <tr>
                  <th>产品简称</th><th>公司到货量（曲周）</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, i) in parsedExcelData" :key="i">
                  <td style="font-weight:bold;">{{ item.name }}</td><td>{{ item.company_quantity }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div v-if="isImporting" style="margin-top: 15px; text-align: center; color: #409eff; font-weight: bold;">
          正在创建批次并导入数据... ({{ importProgress }} / {{ parsedExcelData.length }})
        </div>

        <div class="modal-actions" v-if="!isImporting">
          <button class="btn" @click="closeBatchForm">取消</button>
          <button class="btn btn-primary" @click="editingBatchId ? updateBatch() : createBatchWithImport()" :disabled="!batchForm.name || !batchForm.arrival_time || isImporting || importErrors.length">
            {{ editingBatchId ? '保存修改' : (importFile ? '确认创建导入批次' : '创建手动批次') }}
          </button>
        </div>
        <p v-if="batchMsg" :style="batchMsgOk ? 'color:#67c23a; margin-top:10px;' : 'color:#f56c6c; margin-top:10px;'">{{ batchMsg }}</p>
      </div>
    </div>


    <div v-if="itemDetailView" class="modal-mask" @click.self="itemDetailView = null">
      <div class="modal-card modal-card-wide">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
          <h3 style="margin:0">{{ itemDetailView.name }}</h3>
          <button class="btn btn-sm" @click="itemDetailView = null">关闭</button>
        </div>
        <div style="margin-bottom:12px;font-size:13px;color:#909399;display:flex;gap:16px;flex-wrap:wrap">
          <span>规格: {{ itemDetailView.spec || '无' }}</span>
          <span>备注: {{ itemDetailView.remark || '无' }}</span>
          <span
            :class="'status-badge ' + (itemDetailView.status === '未分货' ? 'status-pending' : itemDetailView.status === '待报货' ? 'status-warn' : 'status-ok')">{{
              itemDetailView.status }}</span>
        </div>
        <div v-if="employees && employees.length" class="mobile-assign-list">
          <div class="assign-header"
            style="display:flex;font-weight:600;font-size:13px;color:#666;padding:8px 0;border-bottom:1px solid #eee">
            <span style="flex:1">员工</span>
            <span style="width:80px;text-align:center">分货数量</span>
            <span style="width:80px;text-align:center">已报数量</span>
          </div>
          <div v-for="emp in employees" :key="emp.id" class="assign-row"
            style="display:flex;align-items:center;padding:10px 0;border-bottom:1px solid #f0f0f0">
            <span style="flex:1;font-weight:500">{{ emp.display_name || emp.name }}</span>
            <span style="width:80px;text-align:center">
             <input type="text" :value="getItemQty(itemDetailView, emp.id)"
               @input="updateLocalData(itemDetailView, emp.id, $event.target.value)"
               @focus="$event.target.select()"
               @keyup.enter="$event.target.blur()"
               :disabled="selectedBatch?.status === '已关闭'"
               class="cell-input" />
            </span>
            <span style="width:80px;text-align:center;color:#67c23a;font-weight:500">
              {{ getItemActual(itemDetailView, emp.id) }}
              <small v-if="getOriginalActual(itemDetailView, emp.id) !== '-'" class="original-actual">原报 {{ getOriginalActual(itemDetailView, emp.id) }}</small>
              <button v-if="isAssignmentLocked(itemDetailView, emp.id) && selectedBatch?.status !== '已关闭'"
                class="btn btn-xs unlock-button" @click="unlockAssignment(itemDetailView, getAssignment(itemDetailView, emp.id))">解锁</button>
            </span>
          </div>
        </div>
        <div v-if="employees && employees.length"
          style="margin-top:12px;padding-top:12px;border-top:2px solid #409eff;display:flex;justify-content:space-between;font-weight:600;font-size:14px">
          <span>合计</span>
          <div style="display:flex;gap:24px">
            <span style="color:#e6a23c">分货: {{ getItemTotal(itemDetailView) }}</span>
            <span style="color:#67c23a">报货: {{ getItemActualTotal(itemDetailView) }}</span>
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn" @click="itemDetailView = null">取消</button>
          <button class="btn btn-primary" @click="saveAllAssignments" :disabled="hasAllocationErrors || selectedBatch?.status === '已关闭'">保存分货</button>
        </div>
      </div>
  
    </div>
  <div v-if="editingItem" class="modal-mask" @click.self="editingItem = null">
  <div class="modal-card" style="width: 400px;">
    <h3>修改货品信息</h3>
    <div class="form-group">
      <label>货品名称</label>
      <input v-model="itemEditForm.name" />
    </div>
    <div class="form-group">
      <label>备注</label>
      <input v-model="itemEditForm.remark" />
    </div>
    <div class="modal-actions">
      <button class="btn" @click="editingItem = null">取消</button>
      <button class="btn btn-primary" @click="saveItemEdit">保存修改</button>
    </div>
  </div>
</div>
  </div>
</template>

<script>
import * as XLSX from 'xlsx'

const API = "/api"

function authHeaders(extra = {}) {
  const token = localStorage.getItem("token")
  return token ? { ...extra, Authorization: `Bearer ${token}` } : extra
}

async function parseApiResponse(response) {
  const data = await response.json().catch(() => ({}))
  if (response.status === 401) {
    localStorage.removeItem("token")
    localStorage.removeItem("user")
    window.location.hash = "#/login"
  }
  if (!response.ok) {
    const error = new Error(data.error || response.statusText || "请求失败")
    error.errors = data.errors || []
    throw error
  }
  return data
}

async function apiGet(url) {
  return parseApiResponse(await fetch(url, { headers: authHeaders() }));
}

async function apiPost(url, body) {
  return parseApiResponse(await fetch(url, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body)
  }));
}

async function apiUpload(url, formData) {
  return parseApiResponse(await fetch(url, {
    method: "POST",
    headers: authHeaders(),
    body: formData
  }));
}

async function apiPut(url, body) {
  return parseApiResponse(await fetch(url, {
    method: "PUT",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body)
  }));
}

async function apiDelete(url) {
  return parseApiResponse(await fetch(url, { method: "DELETE", headers: authHeaders() }));
}

export default {
  data() {
    return {
      user: JSON.parse(localStorage.getItem("user") || "{}"),
      mobilePageTitle: "分单系统",
      currentPage: "dashboard",
      batches: [],
      selectedBatchId: null,
      items: [],
      employees: [],
      cargoTypes: [],
      unitTypes: [],
      cargoForm: { name: "", default_unit: "" },
      unitForm: { name: "" },
      empForm: { display_name: "", phone: "" },
      showCargoEditModal: false,
      cargoEditForm: { id: null, name: "", default_unit: "" },
      cargoEditMsg: "",
      showUnitEditModal: false,
      unitEditForm: { id: null, name: "" },
      unitEditMsg: "",
      showEmpEditModal: false,
      empEditForm: { id: null, display_name: "", phone: "" },
      empEditMsg: "",
      cargoMsg: "", empMsg: "", unitMsg: "",
      cargoMsgError: false, empMsgError: false, unitMsgError: false,
      showBatchForm: false,
      editingBatchId: null,
      batchForm: { name: "", arrival_time: new Date().toISOString().slice(0, 10), batch_remark: "" },
      batchMsg: "", batchMsgOk: false,
      showItemForm: false,
      itemForm: { name: "", spec: "", unit: "", remark: "" },
      showAssignmentModal: false,
      assignItem: null,
      assignmentForm: [],
      assignMsg: "",
      sidebarOpen: false,
      employeeSearch: "",
      itemSearch: "",
      itemStatusFilter: "all",
      summaryData: null,
      summaryBatchId: null,
      itemDetailView: null,
      mobileItemId: null,

      parsedExcelData: [],
      importFile: null,
      importErrors: [],
      manualItems: [],
      selectedCargoTypeId: "",
      matchedEmployees: [],
      unmatchedEmployees: [],
      isImporting: false,
      importProgress: 0,
      editingItem: null, // 当前编辑的行对象
  itemEditForm: { name: "", remark: "" } // 编辑表单
    }
  },
  computed: {
    stats() {
      const totalBatches = this.batches.length
      const latestBatch = this.sortedBatches.length ? this.sortedBatches[0] : null
      const totalItems = latestBatch ? (latestBatch.item_count || 0) : 0
      let pendingItems = 0, doneItems = 0
      for (const item of this.items) {
        if (item.status === "待报货") pendingItems++
        else if (item.status === "已完成") doneItems++
      }
      return { totalBatches, totalItems, pendingItems, doneItems, latestBatchName: latestBatch ? latestBatch.name : '' }
    },
    matrixEmployees() {
      const order = {}
      this.employees.forEach((e, i) => { order[e.id] = i })
      return this.employees.filter(e => e.role === 'employee' && e.is_active)
        .map(e => ({ id: e.id, name: e.display_name || e.name }))
    },
    summaryEmployees() {
      if (!this.summaryData?.employee_totals) return []
      return this.summaryData.employee_totals.map(employee => ({
        id: employee.user_id,
        name: employee.user_name,
        allocated_quantity: employee.allocated_quantity,
        actual_quantity: employee.actual_quantity,
      }))
    },
    activeUnitTypes() {
      return this.unitTypes.filter(unit => unit.is_active)
    },
    sortedBatches() {
      return [...this.batches].sort((a, b) => {
        const da = a.arrival_time || ''
        const db = b.arrival_time || ''
        return db.localeCompare(da) || (b.id - a.id)
      })
    },
    selectedBatch() {
      return this.batches.find(batch => batch.id === Number(this.selectedBatchId)) || null
    },
    filteredItems() {
      const keyword = this.itemSearch.toLowerCase()
      return this.items.filter(item => {
        if (keyword && !String(item.name || "").toLowerCase().includes(keyword)) return false
        if (this.itemStatusFilter === "over") return this.getItemRemaining(item) < 0
        if (this.itemStatusFilter === "pending") return item.status === "待报货"
        if (this.itemStatusFilter === "done") return item.status === "已完成"
        if (this.itemStatusFilter === "unallocated") return item.status === "未分货"
        return true
      })
    },
    hasAllocationErrors() {
      return this.items.some(item => this.getItemRemaining(item) < 0 || !this.isCompanyQuantityValid(item))
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
  startEdit(item) {
    this.editingItem = item;
    this.itemEditForm = { name: item.name, remark: item.remark || "" };
  },

  async saveItemEdit() {
    try {
      const payload = {
        name: this.itemEditForm.name,
        remark: this.itemEditForm.remark,
        spec: this.editingItem.spec, // 保持原规格
        unit: this.editingItem.unit  // 保持原单位
      };
      
      // 调用 API 更新数据
      await apiPut(API + "/items/" + this.editingItem.id, payload);
      
      // 更新本地数据
      this.editingItem.name = this.itemEditForm.name;
      this.editingItem.remark = this.itemEditForm.remark;
      
      this.editingItem = null;
      alert("修改成功");
      await this.loadItems(this.selectedBatchId);
    } catch (e) {
      alert("修改失败: " + e.message);
    }
  },
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
    
    closeBatchForm() {
      if(this.isImporting) return; 
      this.showBatchForm = false;
      this.parsedExcelData = [];
      this.matchedEmployees = [];
      this.unmatchedEmployees = [];
      this.importFile = null;
      this.importErrors = [];
      this.manualItems = [];
      this.selectedCargoTypeId = "";
    },

    showBatchFormForCreate() {
      this.editingBatchId = null
      this.batchForm = { name: "", arrival_time: new Date().toISOString().slice(0, 10), batch_remark: "" }
      this.batchMsg = ""
      this.parsedExcelData = [];
      this.matchedEmployees = [];
      this.unmatchedEmployees = [];
      this.importFile = null;
      this.importErrors = [];
      this.manualItems = [];
      this.selectedCargoTypeId = "";
      this.showBatchForm = true
    },
    editBatch(b) {
      this.editingBatchId = b.id
      const dateStr = b.arrival_time || ""
      this.batchForm = {
        name: b.name || "",
        arrival_time: b.arrival_time || "",
        batch_remark: b.batch_remark || ""
      }
      this.batchMsg = ""
      this.showBatchForm = true
    },
    addManualItem() {
      const cargoType = this.cargoTypes.find(c => c.id === Number(this.selectedCargoTypeId) && c.is_active)
      if (!cargoType) return
      if (this.manualItems.some(item => item.cargo_type_id === cargoType.id)) {
        this.batchMsg = "同一产品不能重复选择";
        this.batchMsgOk = false;
        return
      }
      this.manualItems.push({
        cargo_type_id: cargoType.id,
        name: cargoType.name,
        unit: cargoType.default_unit || "",
        company_quantity: "",
      })
      this.selectedCargoTypeId = ""
    },
    getPreviewQty(item, empId) {
      const assign = item.assignments.find(a => a.user_id === empId);
      return assign ? assign.allocated_quantity : '-';
    },
    getPreviewActualQty(item, empId) {
      const assign = item.assignments.find(a => a.user_id === empId);
      return assign ? assign.actual_quantity : '-';
    },
    handleFileUpload(event) {
      const file = event.target.files[0];
      if (!file) return;
      this.importFile = file;
      this.importErrors = [];
      this.parsedExcelData = [];
      const form = new FormData();
      form.append("file", file);
      apiUpload(API + "/batches/import/validate", form)
        .then(data => {
          this.parsedExcelData = data.items || [];
          if (!this.batchForm.name) this.batchForm.name = data.reference_name || "";
        })
        .catch(error => {
          this.importFile = null;
          this.importErrors = error.errors || [{ reason: error.message || "Excel 校验失败" }];
          this.batchMsg = "Excel 校验失败，请查看全部错误后重新选择文件。";
          this.batchMsgOk = false;
        });
    },

    getPreviewQty(item, empId) {
      const assign = item.assignments.find(a => a.user_id === empId);
      return assign ? assign.allocated_quantity : '-';
    },

    async createBatchWithImport() {
      try {
        this.batchMsg = "";
        this.isImporting = true;
        let createdBatch;
        if (this.importFile) {
          const form = new FormData();
          form.append("file", this.importFile);
          form.append("name", this.batchForm.name);
          form.append("arrival_time", this.batchForm.arrival_time);
          form.append("batch_remark", this.batchForm.batch_remark || "");
          createdBatch = await apiUpload(API + "/batches/import", form);
        } else {
          createdBatch = await apiPost(API + "/batches", {
            name: this.batchForm.name,
            arrival_time: this.batchForm.arrival_time,
            batch_remark: this.batchForm.batch_remark || "",
            source_type: "manual",
            items: this.manualItems.map(item => ({
              cargo_type_id: item.cargo_type_id,
              company_quantity: item.company_quantity,
            })),
          });
        }
        const targetBatchId = createdBatch.id;
        this.batchMsg = "批次创建成功！";
        this.batchMsgOk = true;
        setTimeout(async () => {
          this.isImporting = false;
          this.closeBatchForm();
          await this.loadBatches();
          this.selectBatchById(targetBatchId);
          this.currentPage = 'batches';
        }, 800);

      } catch (e) {
        this.isImporting = false;
        this.batchMsg = e.response?.data?.error || e.message || "创建/导入过程中发生错误";
        this.batchMsgOk = false;
      }
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
        this.closeBatchForm()
        await this.loadBatches()
      } catch (e) {
        this.batchMsg = e.response?.data?.error || "更新失败"
        this.batchMsgOk = false
      }
    },
    
    insertRow() {
      this.items.push({
        id: 'temp_' + Date.now() + Math.floor(Math.random() * 1000),
        name: '',
        status: '未分货',
        remark: '手动插入',
        assignments: [],
        isTemp: true  
      });
      
      setTimeout(() => {
        const wrap = document.querySelector('.matrix-table-wrap');
        if (wrap) wrap.scrollTop = wrap.scrollHeight;
      }, 50);
    },

    async deleteBatch(batch) {
      if (!batch) return
      if (!batch.can_delete) {
        alert("该批次已有分货或报货记录，不能删除；请关闭批次")
        return
      }
      if (!confirm(`确认删除空批次“${batch.name}”？此操作无法恢复。`)) return
      try {
        await apiDelete(API + "/batches/" + batch.id)
        if (this.selectedBatchId === batch.id) { this.selectedBatchId = null; this.items = [] }
        await this.loadBatches()
      } catch (error) {
        alert(error.message || "删除批次失败")
      }
    },
    batchStatusClass(status) {
      if (status === '已完成') return 'status-ok'
      if (status === '已关闭') return 'status-closed'
      return 'status-pending'
    },
    async closeBatch(batch) {
      if (!confirm(`确认关闭“${batch.name}”？关闭后员工只能查看，不能再提交报货。`)) return
      try {
        await apiPost(API + '/batches/' + batch.id + '/close', {})
        await this.loadBatches()
        if (this.selectedBatchId === batch.id) await this.loadItems(batch.id)
        alert('批次已关闭')
      } catch (error) {
        alert(error.message || '关闭批次失败')
      }
    },
    async reopenBatch(batch) {
      if (!confirm(`确认重新打开“${batch.name}”？重新打开后可继续处理该批次。`)) return
      try {
        await apiPost(API + '/batches/' + batch.id + '/reopen', {})
        await this.loadBatches()
        if (this.selectedBatchId === batch.id) await this.loadItems(batch.id)
        alert('批次已重新打开')
      } catch (error) {
        alert(error.message || '重新打开批次失败')
      }
    },
    
    async deleteItem(item) {
      if (item.isTemp) {
        this.items = this.items.filter(i => i.id !== item.id);
        return;
      }
      if (!confirm("确认删除此货品?")) return;
      await apiDelete(API + "/items/" + item.id);
      await this.loadItems(this.selectedBatchId);
      await this.loadBatches();
    },

    updateLocalData(item, userId, newValue) {
      let val = String(newValue).trim();
      if (val === "") val = "-"; 

      if (!item.assignments) item.assignments = [];
      let existingAssign = item.assignments.find(a => a.user_id === userId);
      
      if (existingAssign && String(existingAssign.allocated_quantity) === val) return;
      
      if (existingAssign) {
        existingAssign.allocated_quantity = val;
      } else {
        item.assignments.push({ user_id: userId, allocated_quantity: val });
      }

      if (item.status === "未分货" && val !== "-" && Number(val) > 0) {
        item.status = "待报货";
      }
    },

    async saveAllAssignments() {
      if (this.hasAllocationErrors) {
        alert("请先修正公司到货量或超量分货：总分货不能大于公司到货量。");
        return;
      }
      try {
        const promises = this.items.map(item => {
          const assignmentsPayload = (item.assignments || [])
            .filter(a => a.allocated_quantity !== '-' && a.allocated_quantity !== null && a.allocated_quantity !== "")
            .map(a => ({
                user_id: a.user_id,
                allocated_quantity: Number(a.allocated_quantity)
            }));
          return apiPut(API + "/items/" + item.id + "/assignments", {
            company_quantity: Number(item.company_quantity),
            assignments: assignmentsPayload,
          });
        });
        
        await Promise.all(promises);
        alert("所有分货数据提交成功！");
        await this.loadItems(this.selectedBatchId); 
      } catch (e) {
        console.error("saveAllAssignments failed", e);
        alert("保存过程中出现错误：" + (e.response?.data?.error || e.message || "请检查网络"));
      }
    },

    getAssignment(item, userId) {
      return (item.assignments || []).find(assignment => assignment.user_id === userId) || null
    },
    isAssignmentLocked(item, userId) {
      return this.getAssignment(item, userId)?.report_status === '已锁定'
    },
    async unlockAssignment(item, assignment) {
      if (!assignment) return
      const batchName = this.selectedBatch?.name || '当前批次'
      const actualQuantity = assignment.actual_quantity == null ? '-' : assignment.actual_quantity
      const confirmed = confirm(
        `确认解锁报货？\n批次：${batchName}\n产品：${item.name}\n员工：${assignment.user_name}\n原报货量：${actualQuantity} ${item.unit || ''}\n\n解锁后员工可以重新填写并提交。`
      )
      if (!confirmed) return
      try {
        await apiPost(API + '/assignments/' + assignment.id + '/unlock', {})
        await this.loadItems(this.selectedBatchId)
        await this.loadBatches()
        alert('已解锁，员工可以重新报货')
      } catch (error) {
        alert(error.message || '解锁报货失败')
      }
    },
    getItemQty(item, userId) {
      if (!item.assignments) return '-';
      const a = this.getAssignment(item, userId);
      if (a && a.allocated_quantity !== null && a.allocated_quantity !== undefined && a.allocated_quantity !== "") {
        return a.allocated_quantity;
      }
      return '-';
    },
    getItemActual(item, userId) {
      if (!item.assignments) return '-';
      const a = this.getAssignment(item, userId);
      if (a?.report_status === '已锁定' && a.actual_quantity !== null && a.actual_quantity !== undefined && a.actual_quantity !== "") {
        return a.actual_quantity;
      }
      return '-';
    },
    getOriginalActual(item, userId) {
      const a = this.getAssignment(item, userId);
      if (a?.report_status === '已解锁待重报' && a.actual_quantity !== null && a.actual_quantity !== undefined && a.actual_quantity !== '') {
        return a.actual_quantity;
      }
      return '-';
    },
    
    getItemTotal(item) {
      if (!item.assignments) return '-';
      let sum = 0, hasVal = false;
      item.assignments.forEach(a => {
        if (a.allocated_quantity !== '-' && a.allocated_quantity != null && a.allocated_quantity !== '') {
          sum += Number(a.allocated_quantity); hasVal = true;
        }
      });
      return hasVal ? sum : '-';
    },
    getItemActualTotal(item) {
      if (!item.assignments) return '-';
      let sum = 0, hasVal = false;
      item.assignments.forEach(a => {
        if (a.report_status === '已锁定' && a.actual_quantity !== '-' && a.actual_quantity != null && a.actual_quantity !== '') {
          sum += Number(a.actual_quantity); hasVal = true;
        }
      });
      return hasVal ? sum : '-';
    },
    isCompanyQuantityValid(item) {
      const value = String(item.company_quantity ?? "").trim();
      if (!value) return false;
      const number = Number(value);
      return Number.isFinite(number) && number >= 0 && Math.round(number * 10) === number * 10;
    },
    getItemRemaining(item) {
      if (!this.isCompanyQuantityValid(item)) return '-';
      const allocated = this.getItemTotal(item);
      const total = allocated === '-' ? 0 : Number(allocated);
      return Math.round((Number(item.company_quantity) - total) * 10) / 10;
    },
    getCompanyGrandTotal() {
      return this.items.reduce((total, item) => total + (this.isCompanyQuantityValid(item) ? Number(item.company_quantity) : 0), 0);
    },
    getRemainingGrandTotal() {
      return this.items.reduce((total, item) => {
        const remaining = this.getItemRemaining(item);
        return total + (remaining === '-' ? 0 : Number(remaining));
      }, 0);
    },
    getColumnTotal(userId) {
      let sum = 0, hasVal = false;
      for (const item of this.items) {
        if (item.assignments) {
          const a = item.assignments.find(a => a.user_id === userId);
          if (a && a.allocated_quantity !== '-' && a.allocated_quantity != null && a.allocated_quantity !== '') {
            sum += Number(a.allocated_quantity); hasVal = true;
          }
        }
      }
      return hasVal ? sum : '-';
    },
    getMatrixColumnActualTotal(userId) {
      let sum = 0, hasVal = false;
      for (const item of this.items) {
        if (item.assignments) {
          const a = item.assignments.find(a => a.user_id === userId);
          if (a?.report_status === '已锁定' && a.actual_quantity !== '-' && a.actual_quantity != null && a.actual_quantity !== '') {
            sum += Number(a.actual_quantity); hasVal = true;
          }
        }
      }
      return hasVal ? sum : '-';
    },
    getGrandTotal() {
      let sum = 0, hasVal = false;
      for (const item of this.items) {
        if (item.assignments) {
          for (const a of item.assignments) {
            if (a.allocated_quantity !== '-' && a.allocated_quantity != null && a.allocated_quantity !== '') {
              sum += Number(a.allocated_quantity); hasVal = true;
            }
          }
        }
      }
      return hasVal ? sum : '-';
    },
    getMatrixGrandActualTotal() {
      let sum = 0, hasVal = false;
      for (const item of this.items) {
        if (item.assignments) {
          for (const a of item.assignments) {
            if (a.report_status === '已锁定' && a.actual_quantity !== '-' && a.actual_quantity != null && a.actual_quantity !== '') {
              sum += Number(a.actual_quantity); hasVal = true;
            }
          }
        }
      }
      return hasVal ? sum : '-';
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
      const payload = this.assignmentForm
        .filter(a => a.user_id && a.allocated_quantity !== '-' && a.allocated_quantity !== '')
        .map(a => ({ user_id: Number(a.user_id), allocated_quantity: Number(a.allocated_quantity) || 0 }));
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
      const generatedAt = new Date().toLocaleString('zh-CN', { hour12: false })
      win.document.write('<html><head><meta charset="UTF-8">')
      win.document.write("<style>@page{size:landscape}body{font-family:sans-serif;padding:20px}h2{text-align:center;font-size:16px;margin-bottom:8px}p{text-align:center;font-size:12px;color:#666;margin-bottom:12px}table{width:100%;border-collapse:collapse;font-size:12px}th,td{border:1px solid #000;padding:3px 4px;text-align:center;font-size:11px}th{background:#d9e1f2;font-weight:700}td{vertical-align:middle}.sum-name{text-align:left}.sum-total{font-weight:600}</style></head><body>")
      win.document.write("<h2>" + title + "</h2>")
      win.document.write("<p>" + (arrival ? "到货时间: " + arrival + "　" : "") + "生成时间: " + generatedAt + "</p>")
      win.document.write(table.outerHTML)
      win.document.write("</body></html>")
      win.document.close()
      setTimeout(() => { win.print(); win.close() }, 300)
    },
    async addCargoType() {
      if (!this.cargoForm.name.trim()) { this.cargoMsg = "请输入产品名称"; this.cargoMsgError = true; return }
      try {
        await apiPost(API + "/cargo-types", this.cargoForm)
        this.cargoForm = { name: "", default_unit: "" }
        this.cargoMsg = "产品添加成功"
        this.cargoMsgError = false
        await this.loadCargoTypes()
      } catch (e) { this.cargoMsg = e.message || "添加失败"; this.cargoMsgError = true }
    },
    editCargoType(cargo) {
      this.cargoEditForm = { id: cargo.id, name: cargo.name, default_unit: cargo.default_unit || "" }
      this.cargoEditMsg = ""
      this.showCargoEditModal = true
    },
    async saveCargoEdit() {
      if (!this.cargoEditForm.name.trim()) { this.cargoEditMsg = "产品名称不能为空"; return }
      try {
        await apiPut(API + "/cargo-types/" + this.cargoEditForm.id, {
          name: this.cargoEditForm.name,
          default_unit: this.cargoEditForm.default_unit,
        })
        this.showCargoEditModal = false
        this.cargoMsg = "产品信息已更新"
        this.cargoMsgError = false
        await this.loadCargoTypes()
      } catch (e) { this.cargoEditMsg = e.message || "修改失败" }
    },
    async toggleCargoType(cargo) {
      if (cargo.is_active && !confirm(`停用“${cargo.name}”后将不能用于新建批次，历史批次不受影响。确认停用？`)) return
      try {
        await apiPut(API + "/cargo-types/" + cargo.id, { is_active: !cargo.is_active })
        this.cargoMsg = cargo.is_active ? "产品已停用，历史数据已保留" : "产品已启用"
        this.cargoMsgError = false
        await this.loadCargoTypes()
      } catch (e) { this.cargoMsg = e.message || "操作失败"; this.cargoMsgError = true }
    },
    async addUnitType() {
      if (!this.unitForm.name.trim()) { this.unitMsg = "请输入单位名称"; this.unitMsgError = true; return }
      try {
        await apiPost(API + "/unit-types", this.unitForm)
        this.unitForm = { name: "" }
        this.unitMsg = "单位添加成功"
        this.unitMsgError = false
        await this.loadUnitTypes()
      } catch (e) { this.unitMsg = e.message || "添加失败"; this.unitMsgError = true }
    },
    editUnitType(ut) {
      this.unitEditForm = { id: ut.id, name: ut.name }
      this.unitEditMsg = ""
      this.showUnitEditModal = true
    },
    async saveUnitEdit() {
      if (!this.unitEditForm.name.trim()) { this.unitEditMsg = "单位名称不能为空"; return }
      try {
        await apiPut(API + "/unit-types/" + this.unitEditForm.id, { name: this.unitEditForm.name })
        this.showUnitEditModal = false
        this.unitMsg = "单位信息已更新"
        this.unitMsgError = false
        await this.loadUnitTypes()
      } catch (e) { this.unitEditMsg = e.message || "修改失败" }
    },
    async toggleUnitType(unit) {
      if (unit.is_active && !confirm(`停用“${unit.name}”后将不能用于新产品，历史批次不受影响。确认停用？`)) return
      try {
        await apiPut(API + "/unit-types/" + unit.id, { is_active: !unit.is_active })
        this.unitMsg = unit.is_active ? "单位已停用，历史数据已保留" : "单位已启用"
        this.unitMsgError = false
        await this.loadUnitTypes()
      } catch (e) { this.unitMsg = e.message || "操作失败"; this.unitMsgError = true }
    },
    async addEmployee() {
      if (!this.empForm.display_name) {
        alert("请输入员工姓名");
        return;
      }
      if (!/^1[3-9]\d{9}$/.test(this.empForm.phone)) {
        alert("请输入正确的11位员工手机号");
        return;
      }

      try {
        await apiPost(API + "/employees", this.empForm)
        this.empForm = { display_name: "", phone: "" }
        this.empMsg = "添加成功！员工将使用微信手机号快捷登录"
        this.empMsgError = false
        this.loadEmployees()
        setTimeout(() => { this.empMsg = "" }, 3000);
      } catch (e) {
        this.empMsg = e.message || "添加失败，该手机号可能已存在";
        this.empMsgError = true;
      }
    },
    async toggleEmployee(employee) {
      if (employee.is_active && !confirm(`停用“${employee.display_name}”后将无法登录，历史记录不受影响。确认停用？`)) return
      try {
        await apiPut(API + "/employees/" + employee.id, { is_active: !employee.is_active })
        this.empMsg = employee.is_active ? "员工已停用，历史记录已保留" : "员工已启用"
        this.empMsgError = false
        await this.loadEmployees()
      } catch (e) { this.empMsg = e.message || "操作失败"; this.empMsgError = true }
    },
    editEmployee(e) {
      this.empEditForm = {
        id: e.id,
        display_name: e.display_name,
        phone: e.phone || e.username
      };
      this.empEditMsg = "";
      this.showEmpEditModal = true;
    },
    async saveEmployeeEdit() {
      if (!this.empEditForm.display_name) {
        this.empEditMsg = "姓名不能为空";
        return;
      }
      if (!/^1[3-9]\d{9}$/.test(this.empEditForm.phone)) {
        this.empEditMsg = "请输入正确的11位员工手机号";
        return;
      }
      
      try {
        const payload = {
          display_name: this.empEditForm.display_name,
          phone: this.empEditForm.phone,
        };

        await apiPut(API + "/employees/" + this.empEditForm.id, payload);
        
        this.showEmpEditModal = false;
        this.loadEmployees(); 
        
        this.empMsg = "信息修改成功！";
        this.empMsgError = false;
        setTimeout(() => { this.empMsg = ""; }, 3000);
      } catch (e) {
        this.empEditMsg = e.message || "修改失败，手机号可能被占用";
      }
    },
    
    getAlloc(d, userId) {
      if (!d.assignments) return '-';
      const a = d.assignments.find(a => a.user_id === userId);
      return (a && a.allocated_quantity !== null && a.allocated_quantity !== undefined && a.allocated_quantity !== '') ? a.allocated_quantity : '-';
    },
    getActual(d, userId) {
      if (!d.assignments) return '-';
      const a = d.assignments.find(a => a.user_id === userId);
      return (a?.report_status === '已锁定' && a.actual_quantity !== null && a.actual_quantity !== undefined && a.actual_quantity !== '') ? a.actual_quantity : '-';
    },
    getAllocTotal(d) {
      if (!d.assignments) return '-';
      let sum = 0, hasVal = false;
      d.assignments.forEach(a => {
        let v = a.allocated_quantity;
        if (v !== '-' && v != null && v !== '') {
          sum += Number(v); hasVal = true;
        }
      });
      return hasVal ? sum : '-';
    },
    getColumnAllocTotal(userId) {
      if (!this.summaryData || !this.summaryData.details) return '-';
      let sum = 0, hasVal = false;
      for (const d of this.summaryData.details) {
        let v = this.getAlloc(d, userId);
        if (v !== '-' && v != null && v !== '') {
          sum += Number(v); hasVal = true;
        }
      }
      return hasVal ? sum : '-';
    },
    getColumnActualTotal(userId) {
      if (!this.summaryData || !this.summaryData.details) return '-';
      let sum = 0, hasVal = false;
      for (const d of this.summaryData.details) {
        let v = this.getActual(d, userId);
        if (v !== '-' && v != null && v !== '') {
          sum += Number(v); hasVal = true;
        }
      }
      return hasVal ? sum : '-';
    },
    getGrandAllocTotal() {
      if (!this.summaryData || !this.summaryData.details) return '-';
      let sum = 0, hasVal = false;
      for (const d of this.summaryData.details) {
        let v = this.getAllocTotal(d);
        if (v !== '-' && v != null && v !== '') {
          sum += Number(v); hasVal = true;
        }
      }
      return hasVal ? sum : '-';
    },
    getGrandActualTotal() {
      if (!this.summaryData || !this.summaryData.details) return '-';
      let sum = 0, hasVal = false;
      for (const d of this.summaryData.details) {
        let v = d.total_actual;
        if (v !== '-' && v != null && v !== '') {
          sum += Number(v); hasVal = true;
        }
      }
      return hasVal ? sum : '-';
    },

    downloadExcel() {
      if (!this.summaryData) return
      const employees = this.summaryEmployees
      const headers = ['序号', '货品名称', '公司到货']
      employees.forEach(emp => headers.push(`${emp.name}-分货`, `${emp.name}-报货`))
      headers.push('总分货', '总报货', '剩余')
      const asNumberOrBlank = value => value === '-' || value === null || value === undefined || value === '' ? null : Number(value)
      const rows = this.summaryData.details.map((detail, index) => [
        index + 1,
        detail.item_name,
        asNumberOrBlank(detail.company_quantity),
        ...employees.flatMap(emp => [
          asNumberOrBlank(this.getAlloc(detail, emp.id)),
          asNumberOrBlank(this.getActual(detail, emp.id)),
        ]),
        asNumberOrBlank(detail.total_allocated),
        asNumberOrBlank(detail.total_actual),
        asNumberOrBlank(detail.remaining_quantity),
      ])
      const totalRow = [
        null,
        '合计',
        asNumberOrBlank(this.summaryData.totals.company_quantity),
        ...employees.flatMap(emp => [
          asNumberOrBlank(emp.allocated_quantity),
          asNumberOrBlank(emp.actual_quantity),
        ]),
        asNumberOrBlank(this.summaryData.totals.allocated_quantity),
        asNumberOrBlank(this.summaryData.totals.actual_quantity),
        asNumberOrBlank(this.summaryData.totals.remaining_quantity),
      ]
      const sheet = XLSX.utils.aoa_to_sheet([
        [this.summaryData.batch_name || '全品类汇总'],
        [`到货时间：${this.summaryData.arrival_time || ''}`],
        headers,
        ...rows,
        totalRow,
      ])
      sheet['!merges'] = [
        { s: { r: 0, c: 0 }, e: { r: 0, c: headers.length - 1 } },
        { s: { r: 1, c: 0 }, e: { r: 1, c: headers.length - 1 } },
      ]
      sheet['!cols'] = headers.map((header, index) => ({ wch: index === 1 ? 22 : Math.max(10, header.length + 2) }))
      const workbook = XLSX.utils.book_new()
      XLSX.utils.book_append_sheet(workbook, sheet, '批次汇总')
      XLSX.writeFile(workbook, `${this.summaryData.batch_name || '全品类汇总'}.xlsx`, { compression: true })
    },
    logout() {
      localStorage.removeItem("user")
      localStorage.removeItem("token")
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
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

/* 临时插入行的输入框样式 */
.name-input {
  width: 100%;
  min-width: 60px;
  padding: 4px;
  border: 1px dashed #409eff;
  border-radius: 4px;
  text-align: center;
  font-size: 13px;
  outline: none;
  font-weight: bold;
}
.name-input:focus {
  border-style: solid;
  background-color: #ecf5ff;
}

.item-name-cell strong {
  display: block;
  width: 100%;
  padding: 4px;
  text-align: left;
  font-weight: bold;
  white-space: normal; /* 允许换行 */
  word-break: break-all; /* 防止长名称撑破单元格 */
}
.sum-name {
  text-align: center !important;
  padding-left: 5px !important;
  padding-right: 5px !important;
  max-width: 7em;
  white-space: normal;
  word-wrap: break-word;
  word-break: break-all;
  margin: 0 auto;
}

.sum-col-name {
  text-align: center !important;
  padding-left: 5px !important;
  padding-right: 5px !important;
}

.matrix-table th.col-name,
.matrix-table td.item-name-cell {
  text-align: center !important;
  padding-left: 5px !important;
  padding-right: 5px !important;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background: #f5f6fa;
  color: #333;
}

.admin-layout {
  display: flex;
  height: 100vh;
}

.sidebar {
  width: 220px;
  background: #1e2a3a;
  color: #ccc;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-logo {
  padding: 20px;
  font-size: 18px;
  font-weight: bold;
  color: #fff;
  border-bottom: 1px solid #2a3a4a;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.mobile-header {
  display: none;
}

.hamburger {
  display: none;
}

.item-name-cell {
  cursor: default;
}

.sidebar-nav {
  flex: 1;
  padding: 12px 0;
  overflow-y: auto;
}

.sidebar-nav a {
  display: block;
  padding: 10px 20px;
  color: #aaa;
  cursor: pointer;
  text-decoration: none;
  font-size: 14px;
  transition: 0.2s;
}

.sidebar-nav a:hover {
  background: #2a3a4a;
  color: #fff;
}

.sidebar-nav a.active {
  background: #3a4a5a;
  color: #fff;
  border-left: 3px solid #409eff;
}

.sidebar-section-label {
  padding: 12px 20px 4px;
  font-size: 12px;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 1px;
  border-top: 1px solid #2a3a4a;
  margin-top: 8px;
}

.sidebar-footer {
  padding: 16px 20px;
  border-top: 1px solid #2a3a4a;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
}

.main-content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.page-title {
  font-size: 22px;
  margin-bottom: 20px;
}

.stats-row {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  flex: 1;
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.stat-num {
  font-size: 32px;
  font-weight: bold;
  color: #409eff;
}

.stat-label {
  font-size: 13px;
  color: #999;
  margin-top: 4px;
}

.card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  margin-bottom: 16px;
}

.card h3 {
  margin-bottom: 12px;
  font-size: 16px;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.data-table th,
.data-table td {
  padding: 8px 10px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.data-table th {
  background: #fafafa;
  font-weight: 600;
  color: #666;
}

.data-table tr:hover {
  background: #f8f9fb;
}

.batch-layout {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.batch-right {
  flex: 1;
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  overflow-x: auto;
}

.batch-item {
  padding: 12px;
  border-radius: 6px;
  cursor: pointer;
  margin-bottom: 8px;
  border: 1px solid #eee;
  transition: 0.2s;
}

.batch-item:hover {
  border-color: #409eff;
}

.batch-item.active {
  border-color: #409eff;
  background: #ecf5ff;
}

.batch-item-name {
  font-weight: 600;
  font-size: 15px;
}

.batch-item-sub {
  font-size: 12px;
  color: #888;
  margin-top: 2px;
}

.batch-item-meta {
  font-size: 11px;
  color: #aaa;
  margin-top: 2px;
}

.batch-item-actions {
  margin-top: 6px;
  display: flex;
  gap: 6px;
}

.empty-hint {
  text-align: center;
  color: #999;
  padding: 60px 20px;
  font-size: 15px;
}

.btn {
  display: inline-block;
  padding: 6px 14px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background: #fff;
  cursor: pointer;
  font-size: 13px;
  transition: 0.2s;
}

.btn:hover {
  border-color: #409eff;
  color: #409eff;
}

.btn-primary {
  background: #409eff;
  border-color: #409eff;
  color: #fff;
}

.btn-primary:hover {
  background: #66b1ff;
  border-color: #66b1ff;
  color: #fff;
}

.btn-danger {
  background: #f56c6c;
  border-color: #f56c6c;
  color: #fff;
}

.btn-danger:hover {
  background: #f78989;
  border-color: #f78989;
  color: #fff;
}

.btn-sm {
  padding: 4px 10px;
  font-size: 12px;
}

.btn-xs {
  padding: 2px 8px;
  font-size: 11px;
}

.status-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
}

.status-pending {
  background: #fdf6ec;
  color: #e6a23c;
}

.status-warn {
  background: #fef0f0;
  color: #f56c6c;
}

.status-ok {
  background: #f0f9eb;
  color: #67c23a;
}

.status-closed {
  background: #f2f4f7;
  color: #475467;
}

.unlock-button {
  display: block;
  width: 100%;
  min-height: 28px;
  margin-top: 4px;
  border-color: #b54708;
  color: #b54708;
  background: #fff;
}

.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal-card {
  background: #fff;
  border-radius: 10px;
  padding: 24px;
  max-width: 90vw;
  max-height: 85vh;
  overflow-y: auto;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
  transition: width 0.3s ease;
}

.modal-card h3 {
  margin-bottom: 16px;
  font-size: 18px;
}

.modal-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  margin-top: 16px;
}

.form-group {
  margin-bottom: 12px;
}

.form-group label {
  display: block;
  font-size: 13px;
  color: #666;
  margin-bottom: 4px;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 14px;
  outline: none;
}

.form-group input:focus,
.form-group select:focus {
  border-color: #409eff;
}

@media print {
  .no-print {
    display: none !important;
  }
}

#print-zone h3 {
  margin-bottom: 8px;
}

#print-zone p {
  color: #888;
  margin-bottom: 12px;
  font-size: 14px;
}

::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-thumb {
  background: #ccc;
  border-radius: 3px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

.batch-select-bar {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
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

.batch-select:focus {
  border-color: #409eff;
}

.matrix-filters {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.matrix-filters label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
}

.matrix-filters input,
.matrix-filters select {
  min-height: 36px;
  padding: 6px 10px;
  border: 1px solid #d0d5dd;
  border-radius: 6px;
  background: #fff;
}

.matrix-table .col-type-alloc {
  background-color: #fff8e1 !important;
}

.matrix-table .col-type-actual {
  background-color: #e8f5e9 !important;
}

.matrix-table th.col-type-alloc {
  background-color: #fff3cd !important;
}

.matrix-table th.col-type-actual {
  background-color: #c8e6c9 !important;
}

.matrix-table .allocation-error-row td {
  background-color: #fff1f0 !important;
}

.quantity-error {
  color: #c4320a;
  font-weight: 700;
}

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

.matrix-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  min-width: 500px;
}

.matrix-table th,
.matrix-table td {
  padding: 3px 3px;
  text-align: center;
 
  border: 1px solid #000;
}

.matrix-table th {
  background: #d9e1f2;
  font-weight: 700;
  color: #333;
  font-size: 12px;
}

.matrix-table thead th {
  border-bottom: 2px solid #000;
}

.matrix-table tbody tr:nth-child(even) {
  background: #f8f9fc;
}

.matrix-table tfoot td {
  background: #eef1f8;
  font-weight: 600;
  border-top: 2px solid #000;
}

.matrix-table tbody tr:hover {
  background: #eef2fa;
}

.matrix-table .col-name {
  text-align: left;
  min-width: 65px;
  width: 120px;
}

.matrix-table .col-emp {
  min-width: 55px;
  background: #ecf5ff;
  color: #409eff;
  font-weight: 600;
  padding: 2px 2px !important;
  font-size: 11px;
}

.emp-header-name {
  font-size: 11px;
}

.emp-header-sub {
  font-size: 9px;
  font-weight: 400;
  color: #99c9ff;
  margin-top: 1px;
}

.matrix-table .col-total {
  min-width: 35px;
  background: #fdf6ec;
  color: #e6a23c;
  font-weight: 600;
}

.matrix-table .col-status {
  min-width: 30px;
}

.matrix-table .col-remark {
  min-width: 50px;
  font-size: 11px;
  color: #909399;
}

.matrix-table .cell-remark {
  max-width: 55px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 11px;
  color: #666;
}

.cell-input {
  width: 36px;
  padding: 2px 1px;
  border: 1px solid #dcdfe6;
  border-radius: 2px;
  font-size: 12px;
  text-align: center;
  outline: none;
  background: #fff;
}

.cell-qty {
  padding: 2px 2px !important;
  vertical-align: top;
}

.cell-qty-row {
  margin-bottom: 1px;
}

.cell-qty-alloc {
  padding: 1px 1px !important;
  vertical-align: top;
}

.cell-qty-actual {
  padding: 1px 2px !important;
  vertical-align: top;
  min-width: 28px;
}

.cell-actual-row {
  padding-top: 1px;
  border-top: 1px dashed #ddd;
}

.actual-qty {
  font-size: 11px;
  color: #67c23a;
  font-weight: 600;
}

.actual-qty::before {
  font-size: 9px;
  color: #999;
  margin-right: 1px;
}

.cell-input:focus {
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

.cell-input:hover {
  border-color: #c0c4cc;
}

.cell-input[type=number] {
  -moz-appearance: textfield;
}

.cell-input::-webkit-inner-spin-button,
.cell-input::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.matrix-table .col-actions {
  min-width: 50px;
  width: 50px;
}

.matrix-table .cell-qty-alloc {
  font-weight: 500;
  color: #303133;
}

.matrix-table .cell-qty-actual {
  font-weight: 500;
  color: #67c23a;
}

.matrix-table .cell-total {
  font-weight: 600;
  color: #e6a23c;
}

.matrix-table .cell-total-actual {
  font-weight: 600;
  color: #67c23a;
}

.action-group {
  display: flex;
  gap: 4px;
  justify-content: center;
}

/* ===== 全品类汇总- 矩阵样式 ===== */
.summary-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.summary-table th,
.summary-table td {
  border: 1px solid #000;
  padding: 2px 3px;
  text-align: center;
  font-size: 12px;
}

.original-actual {
  display: block;
  color: #B54708;
  font-size: 11px;
  font-weight: 400;
  white-space: nowrap;
}

.summary-table thead th {
  background: #d9e1f2;
  font-weight: 700;
  color: #333;
  font-size: 11px;
  border-bottom: 2px solid #000;
}

.summary-table tbody tr:nth-child(even) {
  background: #f8f9fc;
}

.summary-table tfoot td {
  background: #eef1f8;
  font-weight: 600;
  border-top: 2px solid #000;
}

.sum-col-idx {
  width: 35px;
}

.sum-col-name {
  text-align: left;
  min-width: 60px;
  width: 60px;
}

.sum-col-emp {
  min-width: 42px;
  background: #ecf5ff;
  padding: 2px 2px !important;
  font-size: 11px;
}

.sum-col-total {
  min-width: 38px;
  background: #fdf6ec;
  font-weight: 600;
  font-size: 11px;
}

.sum-emp-name {
  font-size: 11px;
  color: #409eff;
}

.sum-emp-sub {
  font-size: 9px;
  color: #99c9ff;
  display: flex;
  justify-content: center;
  gap: 1px;
  margin-top: 1px;
}

.sum-sub-alloc {
  color: #e6a23c;
}

.sum-sub-div {
  color: #ccc;
}

.sum-sub-actual {
  color: #67c23a;
}

.sum-name {
  text-align: left;
  font-weight: 500;
}

.sum-idx {
  color: #909399;
  font-size: 12px;
}

.sum-cell {
  font-size: 13px;
  padding: 6px 4px !important;
}

.sum-cell-alloc {
  color: #e6a23c;
  font-weight: 500;
}

.sum-cell-actual {
  color: #67c23a;
  font-weight: 500;
}

.sum-total {
  font-weight: 600;
  font-size: 13px;
}

.sum-total-alloc {
  color: #e6a23c;
  background: #fdf6ec;
}

.sum-total-actual {
  color: #67c23a;
  background: #f0f9eb;
}

@media print {
  .no-print {
    display: none !important;
  }

  .summary-table {
    font-size: 11px;
  }

  .summary-table th,
  .summary-table td {
    border-color: #000;
    padding: 1px 2px;
  }
}

@media (max-width: 768px) {
  .matrix-filters,
  .matrix-filters label {
    align-items: stretch;
    flex-direction: column;
    width: 100%;
  }

  .matrix-filters input,
  .matrix-filters select {
    width: 100%;
    min-height: 44px;
  }
  .sidebar {
    position: fixed;
    z-index: 1000;
    height: 100vh;
    transform: translateX(-100%);
    transition: transform 0.25s ease;
  }

  .sidebar.open {
    transform: translateX(0);
    box-shadow: 4px 0 20px rgba(0, 0, 0, 0.3);
  }

  .sidebar-logo {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .hamburger {
    display: inline-block;
    background: none;
    border: none;
    color: #fff;
    font-size: 22px;
    cursor: pointer;
    padding: 0 4px;
    line-height: 1;
  }

  .admin-layout {
    flex-direction: column;
  }

  .main-content {
    padding: 12px;
    margin-left: 0;
  }

  .mobile-header {
    display: flex;
    position: relative;
    align-items: center;
    gap: 10px;
    padding: 8px 0 12px;
    border-bottom: 1px solid #eee;
    margin-bottom: 12px;
  }

  .mobile-header .hamburger {
    position: fixed;
    top: 10px;
    left: 10px;
    z-index: 1001;
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255, 255, 255, 0.95);
    border-radius: 6px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
    color: #333;
    font-size: 22px;
  }

  .mobile-title {
    font-size: 16px;
    font-weight: 600;
    color: #303133;
    padding-left: 44px;
  }

  .batch-select-bar {
    flex-wrap: wrap;
    gap: 8px;
    padding: 10px 12px;
  }

  .batch-select-bar select {
    flex: 1;
    min-width: 120px;
    max-width: none;
  }

  .matrix-table-wrap {
    overflow-x: auto;
  }

  .matrix-table {
    font-size: 12px;
    min-width: 400px;
    border: 1px solid #000;
  }

  .matrix-table th,
  .matrix-table td {
    padding: 2px 2px;
    border-color: #000;
  }

  .matrix-table .col-name {
    min-width: 70px;
  }

  .matrix-table .col-emp {
    min-width: 50px;
    font-size: 11px;
  }

  .item-name-cell {
    cursor: pointer;
    color: #409eff;
    text-decoration: underline;
  }

  .card .form-inline,
  .card>div[style*="flex"] {
    flex-direction: column;
    align-items: stretch;
  }

  .card input {
    max-width: none !important;
    width: 100% !important;
  }

  .stats-row {
    flex-wrap: wrap;
  }

  .stat-card {
    min-width: calc(50% - 8px);
  }

  .batch-list-page .data-table,
  .batch-list-page .data-table thead,
  .batch-list-page .data-table tbody,
  .batch-list-page .data-table tr,
  .batch-list-page .data-table th,
  .batch-list-page .data-table td {
    display: block;
  }

  .batch-list-page .data-table thead {
    display: none;
  }

  .batch-list-page .data-table tr {
    background: #fff;
    border-radius: 10px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
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

  .batch-list-page .data-table td:nth-child(2)::before {
    content: "到货时间: ";
    color: #909399;
    font-size: 12px;
  }

  .batch-list-page .data-table td:nth-child(3)::before {
    content: "货品数: ";
    color: #909399;
    font-size: 12px;
  }

  .batch-list-page .data-table td:nth-child(4)::before {
    content: "备注: ";
    color: #909399;
    font-size: 12px;
  }

  .batch-list-page .data-table td:nth-child(5)::before {
    content: "创建: ";
    color: #909399;
    font-size: 12px;
  }

  .batch-list-page .data-table td:last-child {
    padding-top: 10px;
    margin-top: 8px;
    border-top: 1px solid #f0f0f0;
    width: auto;
  }

  .batch-list-page .data-table .cell-remark {
    max-width: none;
  }

  .modal-card {
    width: 95vw !important;
    padding: 16px;
  }

  .modal-card-wide {
    width: 95vw;
    padding: 16px;
  }

  #print-zone .data-table {
    font-size: 12px;
  }

  #print-zone .data-table th,
  #print-zone .data-table td {
    padding: 4px;
  }

  .mobile-assign-list .cell-input {
    width: 60px;
  }
}

.batch-list-page .data-table td {
  vertical-align: middle;
}

.batch-list-page .data-table .cell-remark {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #909399;
  font-size: 12px;
}

.master-form {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.master-table-wrap {
  width: 100%;
  overflow-x: auto;
}

.master-table-wrap .data-table {
  min-width: 680px;
}

.status-badge {
  display: inline-block;
  min-width: 52px;
  padding: 4px 8px;
  border-radius: 999px;
  font-size: 13px;
  text-align: center;
}

.status-badge.is-active {
  color: #16803c;
  background: #ecfdf3;
}

.status-badge.is-inactive {
  color: #667085;
  background: #f2f4f7;
}

.action-cell {
  display: flex;
  gap: 8px;
  align-items: center;
  white-space: nowrap;
}

.btn-status {
  color: #16803c;
  border-color: #16803c;
  background: #fff;
}

.form-message {
  color: #16803c;
  margin-bottom: 10px;
}

.form-message.is-error {
  color: #c4320a;
}

.form-error {
  color: #c4320a;
  margin-top: 8px;
}

.master-edit-modal {
  width: 380px;
}

@media (max-width: 768px) {
  .master-form {
    align-items: stretch;
  }

  .master-form input,
  .master-form button {
    width: 100%;
    max-width: none !important;
    min-height: 44px;
  }

  .action-cell .btn {
    min-height: 44px;
    min-width: 64px;
  }
}
</style>
