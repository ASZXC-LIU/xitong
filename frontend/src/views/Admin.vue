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
                {{ b.name }} (到货: {{ b.arrival_time }} | {{ b.item_count }} 个货)
              </option>
            </select>
            <button class="btn btn-sm btn-primary" @click="showBatchFormForCreate" style="margin-left:10px">+ 新建</button>
            <button class="btn btn-sm" @click="openReportForSelected" style="margin-left:6px"
              :disabled="!selectedBatchId">明细</button>
            <button class="btn btn-sm btn-danger" @click="deleteBatch(selectedBatchId)" style="margin-left:6px"
              :disabled="!selectedBatchId">删除</button>
          </div>

          <div class="batch-right">
            <div v-if="!selectedBatchId" class="empty-hint">请选择一个批次</div>
            <template v-else>
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
                <strong>货品列表</strong>
                <div>
                  <button class="btn btn-sm" @click="insertRow" style="margin-right: 12px; border-color: #67c23a; color: #67c23a; font-weight: 600;">+ 插入行</button>
                  <button class="btn btn-primary" @click="saveAllAssignments">一键提交所有分货</button>
                </div>
              </div>
              <div v-if="items.length === 0" class="empty-hint">暂无货品</div>
              <div v-else class="matrix-table-wrap">
                <table class="matrix-table">
                  <thead>
                    <tr>
                      <th class="col-name">货品名称</th>
                      <th v-for="emp in matrixEmployees" :key="emp.id" class="col-emp" colspan="2">
                        <div class="emp-header-name">{{ emp.name }}</div>
                        <div class="emp-header-sub"><span class="sum-sub-alloc col-type-alloc">分货</span><span
                            class="sum-sub-div">/</span><span class="sum-sub-actual col-type-actual">报货</span></div>
                      </th>
                      <th class="col-total col-type-alloc">总分货</th>
                      <th class="col-total col-type-actual">总报货</th>
                      <th class="col-status">状态</th>
                      <th class="col-remark">备注</th>
                      <th class="col-actions">操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="item in items" :key="item.id">
                      <td class="item-name-cell">
                        <input v-if="item.isTemp" type="text" v-model="item.name" placeholder="货品名称" class="name-input" />
                        <strong v-else @click="showItemDetail(item)">{{ item.name }}</strong>
                      </td>
                      <template v-for="emp in matrixEmployees" :key="emp.id">
                        <td class="cell-qty-alloc col-type-alloc">
                          <input type="text" :value="getItemQty(item, emp.id)"
                            @input="updateLocalData(item, emp.id, $event.target.value)"
                            @focus="$event.target.select()"
                            @keyup.enter="$event.target.blur()"
                            class="cell-input" />
                        </td>
                        <td class="cell-qty-actual col-type-actual">
                          <span class="actual-qty">{{ getItemActual(item, emp.id) }}</span>
                        </td>
                      </template>
                      <td class="cell-total col-type-alloc">{{ getItemTotal(item) }}</td>
                      <td class="cell-total cell-total-actual col-type-actual">{{ getItemActualTotal(item) }}</td>
                      <td><span
                          :class="'status-badge ' + (item.status === '未分配' ? 'status-pending' : item.status === '未报货' ? 'status-warn' : 'status-ok')">{{
                          item.status }}</span></td>
                      <td class="cell-remark">{{ item.remark || '无备注' }}</td>
                      <td>
                        <div class="action-group">
                        <button class="btn btn-xs btn-primary" @click="startEdit(item)" style="margin-right: 4px;">修改</button>
                          <button class="btn btn-xs btn-danger" @click="deleteItem(item)" title="删除此货物">删除</button>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                  <tfoot v-if="items.length > 1">
                    <tr>
                      <td><strong>合计</strong></td>
                      <template v-for="emp in matrixEmployees" :key="emp.id">
                        <td class="cell-total col-type-alloc">{{ getColumnTotal(emp.id) }}</td>
                        <td class="cell-total cell-total-actual col-type-actual">{{ getMatrixColumnActualTotal(emp.id) }}</td>
                      </template>
                      <td class="cell-total col-type-alloc">{{ getGrandTotal() }}</td>
                      <td class="cell-total cell-total-actual col-type-actual">{{ getMatrixGrandActualTotal() }}</td>
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
          <div style="display:flex;gap:8px;margin-bottom:12px">
            <input v-model="cargoForm.name" placeholder="种类名称" style="max-width:200px" />
            <input v-model="cargoForm.default_unit" list="default-unit-list" placeholder="默认单位" style="max-width:200px"
              autocomplete="off" />
            <datalist id="default-unit-list">
              <option v-for="ut in unitTypes" :key="ut.id" :value="ut.name">{{ ut.name }}</option>
            </datalist>
            <button class="btn btn-primary btn-sm" @click="addCargoType">添加</button>
          </div>
          <p v-if="cargoMsg" style="color:#67c23a">{{ cargoMsg }}</p>
          <table class="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>种类名称</th>
                <th>默认单位</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="ct in cargoTypes" :key="ct.id">
                <td>{{ ct.id }}</td>
                <td>{{ ct.name }}</td>
                <td>{{ ct.default_unit }}</td>
                <td><button class="btn btn-sm btn-danger" @click="deleteCargoType(ct.id)">删除</button></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-if="currentPage==='employeeMgmt'">
        <h2 class="page-title">人员管理</h2>
        <div class="card">
          <div style="display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap;">
            <input v-model="empForm.display_name" placeholder="员工姓名" style="max-width:150px" />
            <input v-model="empForm.username" type="number" placeholder="手机号(即登录账号)" style="max-width:180px" />
            <input v-model="empForm.password" type="password" placeholder="密码(默认123456)" style="max-width:150px" />
            <button class="btn btn-primary btn-sm" @click="addEmployee">添加</button>
          </div>
          <p v-if="empMsg" style="color:#67c23a;margin-bottom:10px;">{{ empMsg }}</p>
          <table class="data-table">
            <thead><tr><th>ID</th><th>姓名</th><th>手机号(登录账号)</th><th>角色</th><th>操作</th></tr></thead>
            <tbody>
              <tr v-for="e in employees" :key="e.id">
                <td>{{ e.id }}</td><td>{{ e.display_name }}</td><td>{{ e.username }}</td>
                <td><span :style="e.role === 'admin' ? 'color:#e6a23c;font-weight:bold;' : ''">{{ e.role === 'admin' ? '管理员' : '员工' }}</span></td>
                <td>
                  <button class="btn btn-sm" @click="editEmployee(e)" style="margin-right: 6px; border-color: #409eff; color: #409eff;">编辑</button>
                  <button v-if="e.role !== 'admin'" class="btn btn-sm btn-danger" @click="deleteEmployee(e.id)">删除</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="showEmpEditModal" class="modal-mask" @click.self="showEmpEditModal=false">
          <div class="modal-card" style="width: 350px;">
            <h3>编辑信息</h3>
            <div class="form-group">
              <label>姓名</label>
              <input v-model="empEditForm.display_name" placeholder="姓名" />
            </div>
            <div class="form-group">
              <label>手机号(登录账号)</label>
              <input v-model="empEditForm.username" type="number" placeholder="11位手机号" />
            </div>
            <div class="form-group">
              <label>新密码</label>
              <input v-model="empEditForm.password" type="password" placeholder="不填则代表不修改密码" />
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
          <div style="display:flex;gap:8px;margin-bottom:12px">
            <input v-model="unitForm.name" placeholder="单位名称" style="max-width:200px" />
            <button class="btn btn-primary btn-sm" @click="addUnitType">添加</button>
          </div>
          <p v-if="unitMsg" style="color:#67c23a">{{ unitMsg }}</p>
          <table class="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>单位名称</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="ut in unitTypes" :key="ut.id">
                <td>{{ ut.id }}</td>
                <td>{{ ut.name }}</td>
                <td>
                  <button class="btn btn-sm" @click="editUnitType(ut)">编辑</button>
                  <button class="btn btn-sm btn-danger" @click="deleteUnitType(ut.id)">删除</button>
                </td>
              </tr>
            </tbody>
          </table>
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
              </tr>
            </thead>
            <tbody>
              <tr v-for="(d, idx) in summaryData.details" :key="d.item_name">
                <td class="sum-idx">{{ idx + 1 }}</td>
                <td class="sum-name">{{ d.item_name }}</td>
                <template v-for="emp in summaryEmployees" :key="emp.id">
                  <td class="sum-cell sum-cell-alloc">{{ getAlloc(d, emp.id) }}</td>
                  <td class="sum-cell sum-cell-actual">{{ getActual(d, emp.id) }}</td>
                </template>
                <td class="sum-total sum-total-alloc">{{ getAllocTotal(d) }}</td>
                <td class="sum-total sum-total-actual">{{ d.total_actual ?? '-' }}</td>
              </tr>
            </tbody>
            <tfoot>
              <tr>
                <td></td>
                <td style="text-align:center;font-weight:600;padding:8px 10px">合计</td>
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
                <td>{{ b.created_at?.slice(0, 16) }}</td>
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

    <div v-if="showBatchForm" class="modal-mask" @click.self="closeBatchForm">
      <div class="modal-card" :style="{ width: parsedExcelData.length ? '80vw' : '480px', maxWidth: '1000px' }">
        <h3>{{ editingBatchId ? '编辑批次' : '新建报货批次' }}</h3>
        
        <div style="display:flex; gap:16px; flex-wrap:wrap;">
          <div style="flex:1; min-width:200px;">
            <div class="form-group">
              <label>报货日期 <span style="color:red">*</span></label>
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
            
            <div v-if="!editingBatchId" class="form-group" style="margin-top:20px; padding-top:16px; border-top:1px dashed #ddd;">
              <label style="color:#409eff; font-weight:bold;">批量导入分单 (可选)</label>
              <p style="font-size:12px; color:#888; margin-bottom:8px;">请上传包含货品和人员分货数量的 Excel 文件 (.xlsx, .xls)</p>
              <input type="file" accept=".xlsx, .xls" @change="handleFileUpload" style="padding: 4px;" />
            </div>
          </div>

          <div v-if="parsedExcelData.length > 0 && !editingBatchId" style="flex: 2; border-left: 1px solid #eee; padding-left:16px; max-height: 400px; overflow-y:auto;">
            <h4 style="margin-bottom: 8px; color: #67c23a;">数据预览 (共 {{ parsedExcelData.length }} 条)</h4>
            <div v-if="unmatchedEmployees.length > 0" style="background:#fef0f0; color:#f56c6c; padding:8px; border-radius:4px; font-size:12px; margin-bottom:10px;">
              <strong>注意：</strong> Excel中的列名 <b>{{ unmatchedEmployees.join(', ') }}</b> 未能在系统中匹配到对应员工，该列数据将被忽略。
            </div>
           <table class="data-table" style="font-size:12px;">
              <thead>
                <tr>
                  <th>货品名称</th>
                  <th v-for="emp in matchedEmployees" :key="emp.id">{{ emp.name }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, i) in parsedExcelData" :key="i">
                  <td style="font-weight:bold;">{{ item.name }}</td>
                  <td v-for="emp in matchedEmployees" :key="emp.id">
                    <span style="color:#e6a23c">分: {{ getPreviewQty(item, emp.id) }}</span> / 
                    <span style="color:#67c23a">报: {{ getPreviewActualQty(item, emp.id) }}</span>
                  </td>
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
          <button class="btn btn-primary" @click="editingBatchId ? updateBatch() : createBatchWithImport()" :disabled="!batchForm.batch_date">
            {{ editingBatchId ? '保存修改' : (parsedExcelData.length ? '一键建批次并导入' : '创建批次') }}
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
            :class="'status-badge ' + (itemDetailView.status === '未分配' ? 'status-pending' : itemDetailView.status === '未报货' ? 'status-warn' : 'status-ok')">{{
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
               class="cell-input" />
            </span>
            <span style="width:80px;text-align:center;color:#67c23a;font-weight:500">{{ getItemActual(itemDetailView,
              emp.id) }}</span>
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
import * as XLSX from 'xlsx';

const API = "/api"

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
      empForm: { display_name: "", phone: "", username: "", password: "" },
      showEmpEditModal: false,
      empEditForm: { id: null, display_name: "", username: "", password: "" },
      empEditMsg: "",
      cargoMsg: "", empMsg: "", unitMsg: "",
      showBatchForm: false,
      editingBatchId: null,
      batchForm: { name: "", arrival_time: "", batch_remark: "", batch_date: new Date().toISOString().slice(0, 10) },
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

      parsedExcelData: [],
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
        if (item.status === "未报货") pendingItems++
        else if (item.status === "已完成") doneItems++
      }
      return { totalBatches, totalItems, pendingItems, doneItems, latestBatchName: latestBatch ? latestBatch.name : '' }
    },
    matrixEmployees() {
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
    },

    showBatchFormForCreate() {
      this.editingBatchId = null
      this.batchForm = { name: "", arrival_time: "", batch_remark: "", batch_date: new Date().toISOString().slice(0, 10) }
      this.batchMsg = ""
      this.parsedExcelData = [];
      this.matchedEmployees = [];
      this.unmatchedEmployees = [];
      this.showBatchForm = true
    },
    editBatch(b) {
      this.editingBatchId = b.id
      const dateStr = b.arrival_time || ""
      this.batchForm = {
        name: b.name || "",
        arrival_time: b.arrival_time || "",
        batch_remark: b.batch_remark || "",
        batch_date: dateStr || new Date().toISOString().slice(0, 10)
      }
      this.batchMsg = ""
      this.showBatchForm = true
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

      const reader = new FileReader();
      reader.onload = (e) => {
        const data = new Uint8Array(e.target.result);
        const workbook = XLSX.read(data, { type: 'array' });
        const firstSheetName = workbook.SheetNames[0];
        const worksheet = workbook.Sheets[firstSheetName];
        
        const jsonArr = XLSX.utils.sheet_to_json(worksheet, { header: 1 });
        
        if (jsonArr.length < 2) {
          alert("Excel文件内容太少或格式不正确");
          return;
        }

        const headers = jsonArr[0];
        
        let itemNameColIdx = -1;
        for (let i = 0; i < headers.length; i++) {
          if (headers[i] && String(headers[i]).trim() === '货品名称') {
            itemNameColIdx = i;
            break;
          }
        }
        if (itemNameColIdx === -1) itemNameColIdx = 0;

        this.matchedEmployees = [];
        this.unmatchedEmployees = [];
        const empColumnMap = {}; 

        for (let colIdx = 0; colIdx < headers.length; colIdx++) {
          if (colIdx === itemNameColIdx) continue; 
          
          let colName = headers[colIdx];
          if (!colName) continue;
          colName = String(colName).trim();
          
          const excludeColumns = ['序号', '规格', '单位', '备注', '总计', '合计', '预计到货数量', '总报货', '剩余数量', '总分货数', '货品名称'];
          if (excludeColumns.includes(colName)) continue;

          const matched = this.employees.find(e => {
            const name = (e.display_name || e.name || "").trim();
            return name && colName.includes(name);
          });

          if (matched) {
            empColumnMap[colIdx] = matched.id;
            this.matchedEmployees.push({ id: matched.id, name: matched.display_name || matched.name });
          } else {
            this.unmatchedEmployees.push(colName);
          }
        }

        const parsedItems = [];
        for (let rowIdx = 1; rowIdx < jsonArr.length; rowIdx++) {
          const row = jsonArr[rowIdx];
          
          const itemName = row[itemNameColIdx]; 
          
          if (!itemName || String(itemName).trim() === "") continue;

          const assignments = [];
          for (let colIdx in empColumnMap) {
            let qty = row[colIdx];
            if (qty !== undefined && qty !== null && qty !== '' && String(qty).trim() !== '-') {
              // 🔥 修改 1：同时将该数量赋值给分货(allocated_quantity) 和报货(actual_quantity)
              assignments.push({
                user_id: empColumnMap[colIdx],
                allocated_quantity: Number(qty) || 0,
                actual_quantity: Number(qty) || 0 
              });
            }
          }
          parsedItems.push({ name: String(itemName).trim(), assignments });
        }
        
        this.parsedExcelData = parsedItems;
      };
      reader.readAsArrayBuffer(file);
    },

    getPreviewQty(item, empId) {
      const assign = item.assignments.find(a => a.user_id === empId);
      return assign ? assign.allocated_quantity : '-';
    },

    async createBatchWithImport() {
      try {
        this.batchMsg = "";
        
        const dateStr = this.batchForm.batch_date || new Date().toISOString().slice(0, 10);
        const parts = dateStr.split("-");
        const month = parseInt(parts[1]);
        const day = parseInt(parts[2]);
        this.batchForm.name = month + "月" + day + "日报货";
        
        if (this.parsedExcelData.length === 0) {
          await apiPost(API + "/batches", this.batchForm);
          this.batchMsg = "创建成功!";
          this.batchMsgOk = true;
          this.closeBatchForm();
          await this.loadBatches();
          return;
        }

        this.isImporting = true;
        this.importProgress = 0;

        const createdBatch = await apiPost(API + "/batches", this.batchForm);
        let targetBatchId = createdBatch.id; 
        if (!targetBatchId) {
           await this.loadBatches();
           targetBatchId = this.sortedBatches[0].id; 
        }

        for (let i = 0; i < this.parsedExcelData.length; i++) {
          const rowData = this.parsedExcelData[i];
          
          const foundType = this.cargoTypes.find(c => c.name === rowData.name);
          const itemUnit = foundType && foundType.default_unit ? foundType.default_unit : '个';
          
          const createdItem = await apiPost(API + "/batches/" + targetBatchId + "/items", { 
             name: rowData.name, 
             spec: "", 
             unit: itemUnit, 
             remark: "Excel批量导入" 
          });

          if (rowData.assignments.length > 0 && createdItem.id) {
            await apiPut(API + "/items/" + createdItem.id + "/assignments", rowData.assignments);
          }
          
          this.importProgress = i + 1;
        }

        this.batchMsg = "批次创建与数据导入全部成功!";
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
        var nameVal = this.batchForm.name || ""
        if (this.batchForm.batch_date) {
          var parts = this.batchForm.batch_date.split("-")
          if (parts.length === 3) {
            var month = parseInt(parts[1])
            var day = parseInt(parts[2])
            nameVal = month + "月" + day + "日报货"
          }
        }
        const payload = {
          name: nameVal,
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

    async deleteBatch(id) {
      if (!confirm("确认删除此批次?")) return
      await apiDelete(API + "/batches/" + id)
      if (this.selectedBatchId === id) { this.selectedBatchId = null; this.items = [] }
      this.loadBatches()
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
        item.assignments.push({ user_id: userId, allocated_quantity: val, actual_quantity: "-" });
      }

      if (item.status === "未分货" && val !== "-" && Number(val) > 0) {
        item.status = "未报货";
      }
    },

    async saveAllAssignments() {
      try {
        const tempItems = this.items.filter(i => i.isTemp);
        for (let tItem of tempItems) {
          if (!tItem.name || !tItem.name.trim()) {
            alert("有新增货品的名称为空，请填写完整后再提交！");
            return;
          }
          
          const foundType = this.cargoTypes.find(c => c.name === tItem.name.trim());
          const itemUnit = foundType && foundType.default_unit ? foundType.default_unit : '个';
          
          const createdItem = await apiPost(API + "/batches/" + this.selectedBatchId + "/items", {
            name: tItem.name.trim(),
            spec: "",
            unit: itemUnit, 
            remark: tItem.remark || ""
          });
          tItem.id = createdItem.id;
          tItem.isTemp = false;
        }

        const promises = this.items.map(item => {
          if (!item.assignments || item.assignments.length === 0) return Promise.resolve();
          
          let assignmentsPayload = item.assignments
            .filter(a => a.allocated_quantity !== '-' && a.allocated_quantity !== null && a.allocated_quantity !== "")
            .map(a => {
              // 🔥 修改 2：一键保存时，确保实际报货数量 (actual_quantity) 也不丢失，一起发送给后端
              let payload = {
                user_id: a.user_id,
                allocated_quantity: Number(a.allocated_quantity)
              };
              if (a.actual_quantity !== undefined && a.actual_quantity !== '-' && a.actual_quantity !== null && a.actual_quantity !== "") {
                payload.actual_quantity = Number(a.actual_quantity);
              }
              return payload;
            });
            
          return apiPut(API + "/items/" + item.id + "/assignments", assignmentsPayload);
        });
        
        await Promise.all(promises);
        alert("所有分货数据提交成功！");
        await this.loadItems(this.selectedBatchId); 
      } catch (e) {
        console.error("saveAllAssignments failed", e);
        alert("保存过程中出现错误：" + (e.response?.data?.error || e.message || "请检查网络"));
      }
    },

    getItemQty(item, userId) {
      if (!item.assignments) return '-';
      const a = item.assignments.find(a => a.user_id === userId);
      if (a && a.allocated_quantity !== null && a.allocated_quantity !== undefined && a.allocated_quantity !== "") {
        return a.allocated_quantity;
      }
      return '-';
    },
    getItemActual(item, userId) {
      if (!item.assignments) return '-';
      const a = item.assignments.find(a => a.user_id === userId);
      if (a && a.actual_quantity !== null && a.actual_quantity !== undefined && a.actual_quantity !== "") {
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
        if (a.actual_quantity !== '-' && a.actual_quantity != null && a.actual_quantity !== '') {
          sum += Number(a.actual_quantity); hasVal = true;
        }
      });
      return hasVal ? sum : '-';
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
          if (a && a.actual_quantity !== '-' && a.actual_quantity != null && a.actual_quantity !== '') {
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
            if (a.actual_quantity !== '-' && a.actual_quantity != null && a.actual_quantity !== '') {
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
    
    // 🔥 修改处 3：针对旧弹窗如果还用到的话，也补上对 actual_quantity 的保留
    async saveAssignment() {
      const payload = this.assignmentForm
        .filter(a => a.user_id && a.allocated_quantity !== '-' && a.allocated_quantity !== '')
        .map(a => {
           let pl = { user_id: Number(a.user_id), allocated_quantity: Number(a.allocated_quantity) || 0 };
           if(a.actual_quantity !== undefined && a.actual_quantity !== '-' && a.actual_quantity !== null && a.actual_quantity !== "") {
              pl.actual_quantity = Number(a.actual_quantity);
           }
           return pl;
        });
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
      if (!this.empForm.display_name) {
        alert("请输入员工姓名");
        return;
      }
      if (!/^1[3-9]\d{9}$/.test(this.empForm.username)) {
        alert("请输入正确的11位手机号作为账号");
        return;
      }

      try {
        await apiPost(API + "/employees", this.empForm)
        this.empForm = { display_name: "", username: "", password: "" }
        this.empMsg = "添加成功！默认密码为123456"
        this.loadEmployees()
        setTimeout(() => { this.empMsg = "" }, 3000);
      } catch (e) {
        alert(e.message || "添加失败，该手机号可能已存在");
      }
    },
    async deleteEmployee(id) {
      if (!confirm("确认删除?")) return
      await apiDelete(API + "/employees/" + id)
      this.loadEmployees()
    },
    editEmployee(e) {
      this.empEditForm = {
        id: e.id,
        display_name: e.display_name,
        username: e.username,
        password: "" 
      };
      this.empEditMsg = "";
      this.showEmpEditModal = true;
    },
    async saveEmployeeEdit() {
      if (!this.empEditForm.display_name) {
        this.empEditMsg = "姓名不能为空";
        return;
      }
      if (!/^1[3-9]\d{9}$/.test(this.empEditForm.username)) {
        this.empEditMsg = "请输入正确的11位手机号作为账号";
        return;
      }
      
      try {
        const payload = {
          display_name: this.empEditForm.display_name,
          username: this.empEditForm.username,
        };
        if (this.empEditForm.password) {
          payload.password = this.empEditForm.password;
        }

        await apiPut(API + "/employees/" + this.empEditForm.id, payload);
        
        this.showEmpEditModal = false;
        this.loadEmployees(); 
        
        this.empMsg = "信息修改成功！";
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
      return (a && a.actual_quantity !== null && a.actual_quantity !== undefined && a.actual_quantity !== '') ? a.actual_quantity : '-';
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
      const table = document.getElementById("summary-table")
      if (!table) return
      let html = '<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">'
      html += '<head><meta charset="UTF-8">'
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
</style>