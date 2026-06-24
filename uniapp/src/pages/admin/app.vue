<template>
  <view class="admin-layout">
    <!-- Sidebar overlay -->
    <view v-if="sidebarOpen" class="sidebar-overlay" @click="sidebarOpen=false"></view>
    
    <!-- Sidebar (slide-out) -->
    <view class="sidebar" :class="{ open: sidebarOpen }">
      <view class="sidebar-header">
        <text class="sidebar-title">分单系统</text>
        <text class="sidebar-close" @click="sidebarOpen=false">✕</text>
      </view>
      <scroll-view scroll-y class="sidebar-nav">
        <view :class="'nav-item ' + (currentPage==='dashboard' ? 'active' : '')" @click="goPage('dashboard')">
          <text class="nav-icon">🏠</text><text>首页概览</text>
        </view>
        <view :class="'nav-item ' + (currentPage==='batches' ? 'active' : '')" @click="goPage('batches')">
          <text class="nav-icon">📌</text><text>分单管理</text>
        </view>
        <view :class="'nav-item ' + (currentPage==='batchList' ? 'active' : '')" @click="goPage('batchList')">
          <text class="nav-icon">📋</text><text>分单批次</text>
        </view>
        <view :class="'nav-item ' + (currentPage==='summary' ? 'active' : '')" @click="goPage('summary')">
          <text class="nav-icon">📊</text><text>全品类汇总</text>
        </view>
        <view class="nav-section-label">基础信息</view>
        <view :class="'nav-item ' + (currentPage==='cargoTypes' ? 'active' : '')" @click="goPage('cargoTypes')">
          <text class="nav-icon">📦</text><text>货品种类</text>
        </view>
        <view :class="'nav-item ' + (currentPage==='employeeMgmt' ? 'active' : '')" @click="goPage('employeeMgmt')">
          <text class="nav-icon">👥</text><text>人员管理</text>
        </view>
        <view :class="'nav-item ' + (currentPage==='unitTypes' ? 'active' : '')" @click="goPage('unitTypes')">
          <text class="nav-icon">⚖️</text><text>单位管理</text>
        </view>
      </scroll-view>
      <view class="sidebar-footer">
        <text class="sidebar-user">{{ user.display_name }}</text>
        <button class="btn btn-sm btn-danger" @click="logout">退出</button>
      </view>
    </view>

    <!-- Main content -->
    <view class="main-content">
      <!-- Mobile header with fixed hamburger -->
      <view class="mobile-header" :style="{ paddingTop: (statusBarHeight + 6) + 'px' }">
        <button class="hamburger" @click.stop="sidebarOpen=!sidebarOpen">{{ sidebarOpen ? "✕" : "☰" }}</button>
        <text class="mobile-title">{{ pageTitle }}</text>
      </view>

      <!-- ====== DASHBOARD ====== -->
      <view v-if="currentPage==='dashboard'">
        <text class="page-title">首页概览</text>
        <view class="stats-row">
          <view class="stat-card"><text class="stat-num">{{ stats.totalBatches }}</text><text class="stat-label">总批</text></view>
          <view class="stat-card">
            <text class="stat-num">{{ stats.totalItems }}</text>
            <text class="stat-label">最新货</text>
            <text class="stat-batch-name">{{ stats.latestBatchName }}</text>
          </view>
          <view class="stat-card">
            <text class="stat-num warning">{{ stats.pendingItems }}</text>
            <text class="stat-label">待报</text>
            <text class="stat-batch-name">{{ stats.latestBatchName }}</text>
          </view>
          <view class="stat-card">
            <text class="stat-num success">{{ stats.doneItems }}</text>
            <text class="stat-label">已完</text>
            <text class="stat-batch-name">{{ stats.latestBatchName }}</text>
          </view>
        </view>
        <view class="card">
          <text class="card-title">最近批次</text>
          <view v-if="batches.length">
            <view class="list-row header">
              <text class="lcol-time">分货日期</text>
              <text class="lcol-time">报货日期</text>
              <text class="lcol-time">创建时间</text>
            </view>
            <view v-for="b in batches.slice(0,10)" :key="b.id" class="list-row">
              <text class="lcol-time">{{ b.name || "" }}</text>
              <text class="lcol-time">{{ b.arrival_time || "" }}</text>
              <text class="lcol-time">{{ b.created_at?.slice(0,10) }}</text>
            </view>
          </view>
          <text v-else class="empty-hint">暂无批次</text>
        </view>
      </view>

      <!-- ====== 分单管理 ====== -->
      <view v-if="currentPage==='batches'">
        <text class="page-title">分单管理</text>
        <view class="batch-select-bar">
          <picker @change="onBatchChange" :value="selectedBatchIndex" :range="batchOptions" range-key="label" class="batch-picker">
            <view class="batch-select-text">{{ batchLabel || "-- 请选择批次 --" }}</view>
          </picker>
          <button class="btn btn-sm btn-primary" @click="showBatchForm=true">+ 新建</button>
          <button class="btn btn-sm" @click="openSummaryForSelected" :disabled="!selectedBatchId">明细</button>
          <button class="btn btn-sm btn-danger" @click="doDeleteSelectedBatch" :disabled="!selectedBatchId">删除</button>
        </view>

        <scroll-view scroll-x class="matrix-scroll" v-if="selectedBatchId">
          <view class="matrix-toolbar">
            <text class="matrix-title">货品列表</text>
            <text class="matrix-hint">点击货品名查看详情</text>
          </view>
          <view v-if="items.length===0" class="empty-hint">暂无货品</view>
          <view v-else class="matrix-wrap" id="matrix-table">
            <!-- Header -->
            <view class="matrix-row matrix-header">
              <text class="m-cell cell-name-w">货品名称</text>
              <text class="m-cell cell-unit-w">单位</text>
              <block v-for="emp in matrixEmployees" :key="emp.id">
                <text class="m-cell cell-emp-header-w">{{ emp.name }}</text>
              </block>
              <text class="m-cell cell-total-w col-type-alloc">总分货</text>
              <text class="m-cell cell-total-w col-type-actual">总报货</text>
              <text class="m-cell cell-status-w">状态</text>
              <text class="m-cell cell-remark-w">备注</text>
              <text class="m-cell cell-action-w">操作</text>
            </view>
            <!-- Sub-header -->
            <view class="matrix-row matrix-sub-header">
              <text class="m-cell cell-name-w"></text>
              <text class="m-cell cell-unit-w"></text>
              <block v-for="emp in matrixEmployees" :key="emp.id">
                <text class="m-cell cell-emp-w col-type-alloc sub-label">分货</text>
                <text class="m-cell cell-emp-w col-type-actual sub-label">报货</text>
              </block>
              <text class="m-cell cell-total-w col-type-alloc sub-label">总分</text>
              <text class="m-cell cell-total-w col-type-actual sub-label">总报</text>
              <text class="m-cell cell-status-w"></text>
              <text class="m-cell cell-remark-w"></text>
              <text class="m-cell cell-action-w"></text>
            </view>
            <!-- Data rows -->
            <view v-for="(item, rowIdx) in items" :key="item.id"
                  class="matrix-row matrix-data"
                  @mouseenter="onRowEnter(item)" @mouseleave="onRowLeave">
              <text class="m-cell cell-name-w item-name-cell" @click="showItemDetail(item)">{{ item.name }}</text>
              <text class="m-cell cell-unit-w">{{ item.unit }}</text>
              <block v-for="emp in matrixEmployees" :key="emp.id">
                <view class="m-cell cell-emp-w col-type-alloc"
                      @mouseenter="onCellEnter($event, item, emp, 'alloc')" @mouseleave="onCellLeave">
                  <input type="number" :value="getItemQty(item, emp.id)" step="any" min="0"
                         @blur="saveEdit(item, emp.id, $event)" class="qty-input" />
                </view>
                <view class="m-cell cell-emp-w col-type-actual"
                      @mouseenter="onCellEnter($event, item, emp, 'actual')" @mouseleave="onCellLeave">
                  <text class="actual-qty">{{ getItemActual(item, emp.id) }}</text>
                </view>
              </block>
              <text class="m-cell cell-total-w col-type-alloc"
                    @mouseenter="onCellEnter($event, item, null, 'totalAlloc')" @mouseleave="onCellLeave">{{ getItemTotal(item) }}</text>
              <text class="m-cell cell-total-w col-type-actual"
                    @mouseenter="onCellEnter($event, item, null, 'totalActual')" @mouseleave="onCellLeave">{{ getItemActualTotal(item) }}</text>
              <view class="m-cell cell-status-w">
                <text :class="'badge ' + (item.status==='未分配' ? 'badge-pending' : item.status==='未报货' ? 'badge-warn' : 'badge-ok')">{{ item.status }}</text>
              </view>
              <text class="m-cell cell-remark-w">{{ item.remark || "无备注" }}</text>
              <view class="m-cell cell-action-w">
                <button class="btn btn-xs btn-danger" @click="doDeleteItem(item.id)">删除</button>
              </view>
            </view>
            <!-- Totals row (only show when > 1 item, matching web) -->
            <view v-if="items.length > 1" class="matrix-row matrix-total">
              <text class="m-cell cell-name-w" style="font-weight:600;text-align:center">合计</text>
              <text class="m-cell cell-unit-w"></text>
              <block v-for="emp in matrixEmployees" :key="emp.id">
                <text class="m-cell cell-emp-w col-type-alloc" style="font-weight:600">{{ getColumnTotal(emp.id) }}</text>
                <text class="m-cell cell-emp-w col-type-actual" style="font-weight:600">{{ getColumnActualTotal(emp.id) }}</text>
              </block>
              <text class="m-cell cell-total-w col-type-alloc" style="font-weight:600">{{ getGrandTotal() }}</text>
              <text class="m-cell cell-total-w col-type-actual" style="font-weight:600">{{ getGrandActualTotal() }}</text>
              <view class="m-cell cell-status-w"></view>
              <text class="m-cell cell-remark-w"></text>
              <view class="m-cell cell-action-w"></view>
            </view>
          </view>
        </scroll-view>
        <view v-else class="empty-hint-large">请选择一个批次</view>
      </view>

      <!-- ====== 分单批次 ====== -->
      <view v-if="currentPage==='batchList'">
        <view class="section-header">
          <text class="page-title">分单批次</text>
          <button class="btn btn-sm btn-primary" @click="showBatchForm=true">+ 新建</button>
        </view>
        <view v-if="sortedBatches.length===0" class="empty-hint">暂无数据</view>
        <view v-for="b in sortedBatches" :key="b.id" class="batch-card-item">
          <view class="bci-row">
            <text class="bci-name">发货: {{ b.arrival_time || "未设置" }}</text>
            <text class="bci-arrival">报货: {{ b.arrival_time }}</text>
          </view>
          <view class="bci-row sub">
            <text>货品数: {{ b.item_count }}</text>
            <text class="bci-remark">{{ b.batch_remark || "" }}</text>
            <text class="bci-date">{{ b.created_at?.slice(0,10) }}</text>
          </view>
          <view class="bci-actions">
            <button class="btn btn-xs" @click="editBatch(b)">编辑</button>
            <button class="btn btn-xs btn-danger" @click="doDelete(b)">删除</button>
          </view>
        </view>
      </view>

      <!-- ====== 全品类汇总 ====== -->
      <view v-if="currentPage==='summary'">
        <text class="page-title">全品类汇总</text>
        <view class="batch-select-bar no-print">
          <picker @change="onSummaryBatchChange" :value="summaryBatchIndex" :range="summaryBatchOptions" range-key="label" class="batch-picker">
            <view class="batch-select-text">{{ summaryBatchLabel || "-- 请选择批次 --" }}</view>
          </picker>
          <button class="btn btn-sm btn-primary" @click="doPrint" :disabled="!summaryData">打印</button>
          <!-- #ifdef H5 -->
          <button class="btn btn-sm btn-excel" @click="downloadExcel" :disabled="!summaryData">下载Excel</button>
          <!-- #endif -->
        </view>
        <view v-if="!summaryData" class="empty-hint-large">请选择一个批次查看汇总</view>
        <scroll-view scroll-x v-else class="summary-scroll" id="summary-table-wrap">
          <view class="summary-wrap" id="summary-table">
            <!-- Header -->
            <view class="s-row s-header">
              <text class="s-c s-idx">序号</text>
              <text class="s-c s-name">货品名称</text>
              <text class="s-c s-unit">单位</text>
              <block v-for="emp in summaryEmployees" :key="emp.id">
                <text class="s-c s-emp" colspan="2" style="min-width:70px">{{ emp.name }}</text>
              </block>
              <text class="s-c s-total-alloc">总分货</text>
              <text class="s-c s-total-actual">总报货</text>
            </view>
            <!-- Sub-header -->
            <view class="s-row s-subheader">
              <text class="s-c s-idx"></text>
              <text class="s-c s-name"></text>
              <text class="s-c s-unit"></text>
              <block v-for="emp in summaryEmployees" :key="emp.id">
                <text class="s-c s-emp" style="min-width:70px">
                  <text class="sub-alloc">分货</text><text class="sub-div">/</text><text class="sub-actual">报货</text>
                </text>
              </block>
              <text class="s-c s-total-alloc"></text>
              <text class="s-c s-total-actual"></text>
            </view>
            <!-- Data -->
            <view v-for="(d, idx) in summaryData.details" :key="d.item_name" class="s-row s-data">
              <text class="s-c s-idx">{{ idx+1 }}</text>
              <text class="s-c s-name">{{ d.item_name }}</text>
              <text class="s-c s-unit">{{ d.item_unit }}</text>
              <block v-for="emp in summaryEmployees" :key="emp.id">
                <view class="s-c s-emp" style="min-width:70px;display:flex;justify-content:center;gap:1px">
                  <text class="cell-alloc">{{ getAlloc(d, emp.id) }}</text>
                  <text class="cell-div">/</text>
                  <text class="cell-actual">{{ getActual(d, emp.id) }}</text>
                </view>
              </block>
              <text class="s-c s-total-alloc">{{ getAllocTotal(d) }}</text>
              <text class="s-c s-total-actual">{{ d.total_actual ?? 0 }}</text>
            </view>
            <!-- Total -->
            <view v-if="summaryData.details && summaryData.details.length" class="s-row s-total">
              <text class="s-c s-idx"></text>
              <text class="s-c s-name" style="font-weight:600;text-align:center">合计</text>
              <text class="s-c s-unit"></text>
              <block v-for="emp in summaryEmployees" :key="emp.id">
                <view class="s-c s-emp" style="min-width:70px;display:flex;justify-content:center;gap:1px">
                  <text class="cell-alloc total">{{ getColumnAllocTotal(emp.id) }}</text>
                  <text class="cell-div">/</text>
                  <text class="cell-actual total">{{ getColumnActualTotal(emp.id) }}</text>
                </view>
              </block>
              <text class="s-c s-total-alloc" style="font-weight:600">{{ getGrandAllocTotal() }}</text>
              <text class="s-c s-total-actual" style="font-weight:600">{{ getGrandActualTotal() }}</text>
            </view>
          </view>
        </scroll-view>
      </view>

      <!-- ====== 货品种类 ====== -->
      <view v-if="currentPage==='cargoTypes'">
        <text class="page-title">货品种类管理</text>
        <view class="card">
          <view class="form-inline-card">
            <input class="uni-input inline" v-model="cargoForm.name" placeholder="种类名称" />
            <input class="uni-input inline" v-model="cargoForm.default_unit" placeholder="默认单位" />
            <button class="btn btn-sm btn-primary" @click="addCargoType">添加</button>
          </view>
          <text v-if="cargoMsg" class="success-msg">{{ cargoMsg }}</text>
          <view v-if="cargoTypes.length" class="data-table-card">
            <view class="dtr dth">
              <text class="dtc-id">ID</text>
              <text class="dtc-name">种类名称</text>
              <text class="dtc-unit">默认单位</text>
              <text class="dtc-action">操作</text>
            </view>
            <view v-for="ct in cargoTypes" :key="ct.id" class="dtr">
              <text class="dtc-id">{{ ct.id }}</text>
              <text class="dtc-name">{{ ct.name }}</text>
              <text class="dtc-unit">{{ ct.default_unit || "" }}</text>
              <view class="dtc-action"><button class="btn btn-xs btn-danger" @click="deleteCargoType(ct.id)">删除</button></view>
            </view>
          </view>
          <text v-else class="empty-hint">暂无数据</text>
        </view>
      </view>

      <!-- ====== 人员管理 ====== -->
      <view v-if="currentPage==='employeeMgmt'">
        <text class="page-title">人员管理</text>
        <view class="card">
          <view class="form-inline-card">
            <input class="uni-input inline" v-model="empForm.display_name" placeholder="姓名" />
            <input class="uni-input inline" v-model="empForm.username" placeholder="登录名" />
            <input class="uni-input inline" v-model="empForm.password" type="password" placeholder="密码" />
            <button class="btn btn-sm btn-primary" @click="addEmployee">添加</button>
          </view>
          <text v-if="empMsg" class="success-msg">{{ empMsg }}</text>
          <view v-if="employees.length" class="data-table-card">
            <view class="dtr dth">
              <text class="dtc-id">ID</text>
              <text class="dtc-name">姓名</text>
              <text class="dtc-name">登录</text>
              <text class="dtc-unit">角色</text>
              <text class="dtc-action">操作</text>
            </view>
            <view v-for="e in employees" :key="e.id" class="dtr">
              <text class="dtc-id">{{ e.id }}</text>
              <text class="dtc-name">{{ e.display_name }}</text>
              <text class="dtc-name">{{ e.username }}</text>
              <text class="dtc-unit">{{ e.role }}</text>
              <view class="dtc-action"><button class="btn btn-xs btn-danger" @click="deleteEmployee(e.id)">删除</button></view>
            </view>
          </view>
          <text v-else class="empty-hint">暂无数据</text>
        </view>
      </view>

      <!-- ====== 单位管理 ====== -->
      <view v-if="currentPage==='unitTypes'">
        <text class="page-title">单位管理</text>
        <view class="card">
          <view class="form-inline-card">
            <input class="uni-input inline" v-model="unitForm.name" placeholder="单位名称" />
            <button class="btn btn-sm btn-primary" @click="addUnitType">添加</button>
          </view>
          <text v-if="unitMsg" class="success-msg">{{ unitMsg }}</text>
          <view v-if="unitTypes.length" class="data-table-card">
            <view class="dtr dth">
              <text class="dtc-id">ID</text>
              <text class="dtc-name">单位名称</text>
              <text class="dtc-action">操作</text>
            </view>
            <view v-for="ut in unitTypes" :key="ut.id" class="dtr">
              <text class="dtc-id">{{ ut.id }}</text>
              <text class="dtc-name">{{ ut.name }}</text>
              <view class="dtc-action">
                <button class="btn btn-xs" @click="editUnitType(ut)">编辑</button>
                <button class="btn btn-xs btn-danger" @click="deleteUnitType(ut.id)">删除</button>
              </view>
            </view>
          </view>
          <text v-else class="empty-hint">暂无数据</text>
        </view>
      </view>
    </view>

    <!-- Batch form modal -->
    <view v-if="showBatchForm" class="modal-mask" @click="showBatchForm=false">
      <view class="modal-card" @click.stop>
        <text class="modal-title">{{ batchEditId ? "编辑批次" : "新建报货批次" }}</text>
        <view class="form-group">
          <label>分货日期</label>
          <picker mode="date" :value="batchForm.batch_date" @change="onBatchDateChange">
            <view class="uni-input" style="margin-bottom:12px">{{ batchForm.batch_date || "选择分货日期" }}</view>
          </picker>
        </view>
        <view class="form-group">
          <label>报货日期</label>
          <picker mode="date" :value="batchForm.arrival_time" @change="onArrivalDateChange">
            <view class="uni-input" style="margin-bottom:12px">{{ batchForm.arrival_time || "选择报货日期" }}</view>
          </picker>
        </view>
        <view class="form-group">
          <label>批次名称</label>
          <input class="uni-input" v-model="batchForm.name" placeholder="自动生成或手动输入" />
        </view>
        <view class="modal-actions">
          <button class="btn" @click="showBatchForm=false">取消</button>
          <button class="btn btn-primary" @click="saveBatch">保存</button>
        </view>
      </view>
    </view>

    <!-- Item detail modal -->
    <view v-if="showItemDetail" class="modal-mask" @click="showItemDetail=false">
      <view class="modal-card modal-wide" @click.stop>
        <view class="modal-header-bar">
          <text class="modal-title">{{ detailItem.name }}</text>
          <button class="btn btn-sm" @click="showItemDetail=false">关闭</button>
        </view>
        <view class="detail-info-row">
          <text>单位: {{ detailItem.unit }}</text>
          <text>状态: {{ detailItem.status }}</text>
          <text>备注: {{ detailItem.remark || "无" }}</text>
        </view>
        <view class="detail-table-wrap">
          <view class="detail-header-row">
            <text class="dh-name">员工</text>
            <text class="dh-alloc col-type-alloc">分货</text>
            <text class="dh-actual col-type-actual">报货</text>
          </view>
          <view v-for="a in detailAssignments" :key="a.employee_id" class="detail-data-row">
            <text class="dh-name">{{ a.employee_name }}</text>
            <view class="dh-alloc col-type-alloc">
              <input type="number" :value="a.alloc_quantity" step="any" min="0"
                     @blur="saveDetailAssign(detailItem.id, a.employee_id, $event)"
                     class="qty-input-detail" />
            </view>
            <text class="dh-actual col-type-actual">{{ a.actual_quantity ?? 0 }}</text>
          </view>
          <view class="detail-total-row">
            <text class="dh-name" style="font-weight:600">合计</text>
            <text class="dh-alloc col-type-alloc" style="font-weight:600">{{ detailAllocTotal }}</text>
            <text class="dh-actual col-type-actual" style="font-weight:600">{{ detailActualTotal }}</text>
          </view>
        </view>
      </view>
    </view>

    <!-- Tooltip -->
    <view v-if="tooltip.visible" class="matrix-tooltip" :style="{ left: tooltip.x + 'px', top: tooltip.y + 'px' }">
      <text>{{ tooltip.text }}</text>
    </view>
  </view>
</template>
<script>
import { getStorage, setStorage, removeStorage } from "../../utils/storage"
import { apiGet, apiPost, apiPut, apiDelete } from "../../utils/request"

var PRINT_CSS = '@page{size:landscape}body{font-family:sans-serif;padding:20px}h2{text-align:center;font-size:16px;margin-bottom:8px}p{text-align:center;font-size:12px;color:#666;margin-bottom:12px}table{width:100%;border-collapse:collapse;font-size:12px}th,td{border:1px solid #000;padding:3px 4px;text-align:center;font-size:11px}th{background:#d9e1f2;font-weight:700}td{vertical-align:middle}.sum-name{text-align:left}.sum-total{font-weight:600}'
export default {
  data() {
    return {
      user: {},
      sidebarOpen: false, statusBarHeight: 20,
      currentPage: "dashboard",
      // Batches
      batches: [], selectedBatchId: null, selectedBatchIndex: -1,
      showBatchForm: false, batchEditId: null,
      batchForm: { name: "", arrival_time: "", batch_date: "", batch_remark: "" },
      // Items
      items: [], employees: [],
      showItemDetail: false, detailItem: {}, detailAssignments: [],
      // Summary
      summaryData: null, summaryBatchIndex: -1,
      // Cargo types
      cargoTypes: [], cargoForm: { name: "", default_unit: "" }, cargoMsg: "",
      // Employee mgmt
      employeesList: [], empForm: { display_name: "", username: "", password: "" }, empMsg: "",
      // Unit types
      unitTypes: [], unitForm: { name: "" }, unitMsg: "",
      // Tooltip
      tooltip: { visible: false, text: "", x: 0, y: 0 },
      // Save debounce timers
      saveTimers: {},
      // Operation lock
      operating: false
    }
  },
  computed: {
    pageTitle() {
      var map = {
        dashboard: "首页概览", batches: "分单管理", batchList: "分单批次",
        summary: "全品类汇总", cargoTypes: "货品种类", employeeMgmt: "人员管理", unitTypes: "单位管理"
      }
      return map[this.currentPage] || "分单系统"
    },
    batchOptions() {
      var self = this
      return this.batches.map(function(b) {
        return { label: "报货: " + (b.arrival_time || "") + " | 分货: " + (b.name || b.batch_date || ""), value: b.id }
      })
    },
    batchLabel() {
      if (this.selectedBatchIndex < 0 || this.selectedBatchIndex >= this.batches.length) return ""
      return this.batchOptions[this.selectedBatchIndex].label
    },
    sortedBatches() {
      return [...this.batches].sort(function(a, b) {
        return (b.arrival_time||"").localeCompare(a.arrival_time||"") || (b.id - a.id)
      })
    },
    matrixEmployees() {
      var self = this
      if (!this.employees || !this.employees.length) return []
      return this.employees.map(function(e) {
        return { id: e.id, name: e.display_name || e.name }
      })
    },
    stats() {
      var totalBatches = this.batches.length
      var sorted = [...this.batches].sort(function(a, b) {
        return (b.arrival_time||"").localeCompare(a.arrival_time||"") || (b.id - a.id)
      })
      var latest = sorted.length ? sorted[0] : null
      var totalItems = latest ? (latest.item_count || 0) : 0
      var latestName = latest ? latest.name : ""
      var pending = 0, done = 0
      for (var i = 0; i < this.items.length; i++) {
        if (this.items[i].status === "未报货") pending++
        else if (this.items[i].status === "已完成") done++
      }
      return { totalBatches, totalItems, pendingItems: pending, doneItems: done, latestBatchName: latestName }
    },
    // Summary
    summaryBatchOptions() {
      return this.batches.map(function(b) {
        return { label: "报货: " + (b.arrival_time || "") + " | 分货: " + (b.name || ""), value: b.id }
      })
    },
    summaryBatchLabel() {
      if (this.summaryBatchIndex < 0 || this.summaryBatchIndex >= this.batches.length) return ""
      return this.summaryBatchOptions[this.summaryBatchIndex].label
    },
    summaryEmployees() {
      var self = this
      if (!this.employees || !this.employees.length) return []
      return this.employees.map(function(e) {
        return { id: e.id, name: e.display_name || e.name }
      })
    },
    detailAllocTotal() {
      var s = 0
      for (var i = 0; i < this.detailAssignments.length; i++) {
        s += Number(this.detailAssignments[i].alloc_quantity) || 0
      }
      return s
    },
    detailActualTotal() {
      var s = 0
      for (var i = 0; i < this.detailAssignments.length; i++) {
        s += Number(this.detailAssignments[i].actual_quantity) || 0
      }
      return s
    }
  },
  onShow() {
    this.user = getStorage("user") || {}
    if (!this.user || !this.user.id) {
      uni.navigateTo({ url: "/pages/login/login", redirect: true })
      return
    }
    this.initData()
  },
  methods: {
    // ===== Navigation =====
    goPage(page) {
      this.currentPage = page
      this.sidebarOpen = false
      if (page === "batches") {
        this.loadBatches()
        this.loadEmployees()
        // Auto-select first batch if none selected
        if (!this.selectedBatchId && this.sortedBatches.length > 0) {
          this.selectBatchById(this.sortedBatches[0].id)
        }
      } else if (page === "summary") {
        this.loadBatches()
        this.loadEmployees()
        // Auto-select first batch for summary
        if (this.sortedBatches.length > 0) {
          this.summaryBatchIndex = 0
          this.loadSummaryData()
        }
      } else if (page === "batchList") {
        this.loadBatches()
      } else if (page === "cargoTypes") {
        this.loadCargoTypes()
      } else if (page === "employeeMgmt") {
        this.loadEmployees()
      } else if (page === "unitTypes") {
        this.loadUnitTypes()
      } else if (page === "dashboard") {
        this.initData()
      }
    },
    openSummaryForSelected() {
      if (!this.selectedBatchId) return
      this.currentPage = "summary"
      this.sidebarOpen = false
      // Find index of selected batch
      for (var i = 0; i < this.batches.length; i++) {
        if (this.batches[i].id == this.selectedBatchId) {
          this.summaryBatchIndex = i
          break
        }
      }
      this.loadSummaryData()
    },
    logout() {
      removeStorage("user")
      removeStorage("token")
      uni.navigateTo({ url: "/pages/login/login", redirect: true })
    },
    // ===== Init =====
    async initData() {
      try {
        this.batches = await apiGet("/batches") || []
        this.employees = await apiGet("/employees") || []
        this.cargoTypes = await apiGet("/cargo-types") || []
        this.unitTypes = await apiGet("/unit-types") || []
        // Load latest batch items for stats
        var sorted = [...this.batches].sort(function(a, b) {
          return (b.arrival_time||"").localeCompare(a.arrival_time||"") || (b.id - a.id)
        })
        if (sorted.length) {
          this.items = await apiGet("/batches/" + sorted[0].id + "/items") || []
        }
      } catch (e) {
        console.error("initData error", e)
      }
    },
    // ===== Batch =====
    async loadBatches() {
      try { this.batches = await apiGet("/batches") || [] } catch (e) { console.error(e) }
    },
    async loadEmployees() {
      try { this.employees = await apiGet("/employees") || [] } catch (e) { console.error(e) }
    },
    onBatchDateChange(e) { this.batchForm.batch_date = e.detail.value },
    onArrivalDateChange(e) { this.batchForm.arrival_time = e.detail.value },
    onBatchChange(e) {
      this.selectedBatchIndex = e.detail.value
      if (this.selectedBatchIndex >= 0 && this.selectedBatchIndex < this.batches.length) {
        this.selectedBatchId = this.batches[this.selectedBatchIndex].id
        this.loadMatrixItems()
      }
    },
    selectBatchById(id) {
      this.selectedBatchId = id
      // Find index
      for (var i = 0; i < this.batches.length; i++) {
        if (this.batches[i].id == id) {
          this.selectedBatchIndex = i
          break
        }
      }
      this.loadMatrixItems()
    },
    async loadMatrixItems() {
      if (!this.selectedBatchId) { this.items = []; return }
      try {
        this.items = await apiGet("/batches/" + this.selectedBatchId + "/items") || []
      } catch (e) { console.error(e) }
    },
    editBatch(b) {
      this.batchEditId = b.id
      this.batchForm = { name: b.name || "", arrival_time: b.arrival_time || "", batch_date: b.arrival_time || "", batch_remark: b.batch_remark || "" }
      this.showBatchForm = true
    },
    async saveBatch() {
      try {
        // Auto-calculate name from batch_date
        var nameVal = this.batchForm.name || ""
        if (!nameVal && this.batchForm.batch_date) {
          var parts = this.batchForm.batch_date.split("-")
          if (parts.length === 3) {
            var month = parseInt(parts[1])
            var day = parseInt(parts[2])
            nameVal = month + "月" + day + "日报货"
          }
        }
        var payload = {
          name: nameVal,
          arrival_time: this.batchForm.arrival_time,
          batch_remark: this.batchForm.batch_remark
        }
        if (this.batchEditId) {
          await apiPut("/batches/" + this.batchEditId, payload)
        } else {
          await apiPost("/batches", payload)
        }
        this.showBatchForm = false
        this.batchEditId = null
        this.batchForm = { name: "", arrival_time: "", batch_date: "", batch_remark: "" }
        await this.loadBatches()
        if (this.currentPage === "batches" && this.batches.length) {
          this.selectBatchById(this.batches[0].id)
        }
      } catch (e) { console.error(e) }
    },
    async doDelete(b) {
      if (this.operating) return
      this.operating = true
      try {
        await apiDelete("/batches/" + b.id)
        if (this.selectedBatchId === b.id) { this.selectedBatchId = null; this.selectedBatchIndex = -1; this.items = [] }
        await this.loadBatches()
      } catch (e) { console.error(e) }
      finally { this.operating = false }
    },
    async doDeleteSelectedBatch() {
      if (!this.selectedBatchId || this.operating) return
      this.operating = true
      try {
        await apiDelete("/batches/" + this.selectedBatchId)
        // Auto-select next batch
        this.selectedBatchId = null
        this.selectedBatchIndex = -1
        this.items = []
        await this.loadBatches()
        if (this.sortedBatches.length) {
          this.selectBatchById(this.sortedBatches[0].id)
        }
      } catch (e) { console.error(e) }
      finally { this.operating = false }
    },
    // ===== Matrix operations =====
    getItemQty(item, empId) {
      var assignments = item.assignments || []
      for (var i = 0; i < assignments.length; i++) {
        if (assignments[i].employee_id == empId || assignments[i].user_id == empId) return assignments[i].allocated_quantity || 0
      }
      return 0
    },
    getItemActual(item, empId) {
      var assignments = item.assignments || []
      for (var i = 0; i < assignments.length; i++) {
        if (assignments[i].employee_id == empId || assignments[i].user_id == empId) return assignments[i].actual_quantity ?? 0
      }
      return 0
    },
    getItemTotal(item) {
      var s = 0
      var assignments = item.assignments || []
      for (var i = 0; i < assignments.length; i++) {
        s += Number(assignments[i].allocated_quantity) || 0
      }
      return s
    },
    getItemActualTotal(item) {
      var s = 0
      var assignments = item.assignments || []
      for (var i = 0; i < assignments.length; i++) {
        s += Number(assignments[i].actual_quantity) || 0
      }
      return s
    },
    getColumnTotal(empId) {
      var s = 0
      for (var i = 0; i < this.items.length; i++) {
        s += Number(this.getItemQty(this.items[i], empId)) || 0
      }
      return s
    },
    getColumnActualTotal(empId) {
      var s = 0
      for (var i = 0; i < this.items.length; i++) {
        s += Number(this.getItemActual(this.items[i], empId)) || 0
      }
      return s
    },
    getGrandTotal() {
      var s = 0
      for (var i = 0; i < this.items.length; i++) {
        s += Number(this.getItemTotal(this.items[i])) || 0
      }
      return s
    },
    getGrandActualTotal() {
      var s = 0
      for (var i = 0; i < this.items.length; i++) {
        s += Number(this.getItemActualTotal(this.items[i])) || 0
      }
      return s
    },
    saveEdit(item, empId, event) {
      var val = Number(event.detail.value) || 0
      var key = item.id + "-" + empId
      // Update directly via API
      var assignments = []
      var existing = item.assignments || []
      var found = false
      for (var i = 0; i < existing.length; i++) {
        if (existing[i].employee_id == empId || existing[i].user_id == empId) {
          assignments.push({ employee_id: empId, quantity: val })
          found = true
        } else {
          assignments.push({ employee_id: existing[i].employee_id || existing[i].user_id, quantity: existing[i].allocated_quantity || 0 })
        }
      }
      if (!found) {
        assignments.push({ employee_id: empId, quantity: val })
      }
      var self = this
      apiPut("/items/" + item.id + "/assignments", { assignments: assignments }).then(function() {
        self.loadMatrixItems()
      }).catch(function(e) { console.error(e) })
    },
    async doDeleteItem(id) {
      if (this.operating) return
      this.operating = true
      try {
        await apiDelete("/items/" + id)
        await this.loadMatrixItems()
        await this.loadBatches()
      } catch (e) { console.error(e) }
      finally { this.operating = false }
    },
    // ===== Item Detail =====
    showItemDetail(item) {
      if (!item) return
      this.detailItem = item || {}
      var assignments = item.assignments || []
      var das = []
      for (var i = 0; i < this.matrixEmployees.length; i++) {
        var emp = this.matrixEmployees[i]
        var found = null
        for (var j = 0; j < assignments.length; j++) {
          if (assignments[j].employee_id == emp.id || assignments[j].user_id == emp.id) {
            found = assignments[j]
            break
          }
        }
        das.push({
          employee_id: emp.id,
          employee_name: emp.name,
          alloc_quantity: found ? (found.allocated_quantity || 0) : 0,
          actual_quantity: found ? (found.actual_quantity ?? 0) : 0,
        })
      }
      this.detailAssignments = das
      this.showItemDetail = true
    },
    saveDetailAssign(itemId, empId, event) {
      var val = Number(event.detail.value) || 0
      // Update local
      for (var i = 0; i < this.detailAssignments.length; i++) {
        if (this.detailAssignments[i].employee_id == empId) {
          this.detailAssignments[i].alloc_quantity = val
          break
        }
      }
      // Build assignments
      var assignments = []
      for (var i = 0; i < this.detailAssignments.length; i++) {
        assignments.push({ employee_id: this.detailAssignments[i].employee_id, quantity: this.detailAssignments[i].alloc_quantity })
      }
      var self = this
      apiPut("/items/" + itemId + "/assignments", { assignments: assignments }).then(function() {
        self.loadMatrixItems()
      }).catch(function(e) { console.error(e) })
    },
    // ===== Summary =====
    onSummaryBatchChange(e) {
      this.summaryBatchIndex = e.detail.value
      this.loadSummaryData()
    },
    async loadSummaryData() {
      if (this.summaryBatchIndex < 0 || this.summaryBatchIndex >= this.batches.length) return
      var batchId = this.batches[this.summaryBatchIndex].id
      try {
        this.summaryData = await apiGet("/batches/" + batchId + "/report")
      } catch (e) { console.error(e) }
    },
    getAlloc(d, empId) {
      if (!d.employees) return 0
      for (var i = 0; i < d.employees.length; i++) {
        if (d.employees[i].employee_id == empId || d.employees[i].user_id == empId) return d.employees[i].allocated_quantity ?? 0
      }
      return 0
    },
    getActual(d, empId) {
      if (!d.employees) return "-"
      for (var i = 0; i < d.employees.length; i++) {
        if (d.employees[i].employee_id == empId || d.employees[i].user_id == empId) return d.employees[i].actual_quantity ?? "-"
      }
      return "-"
    },
    getAllocTotal(d) {
      if (!d.employees) return 0
      var s = 0
      for (var i = 0; i < d.employees.length; i++) {
        s += Number(d.employees[i].allocated_quantity) || 0
      }
      return s
    },
    getColumnAllocTotal(empId) {
      if (!this.summaryData || !this.summaryData.details) return 0
      var s = 0
      for (var i = 0; i < this.summaryData.details.length; i++) {
        s += Number(this.getAlloc(this.summaryData.details[i], empId)) || 0
      }
      return s
    },
    getColumnActualTotal(empId) {
      if (!this.summaryData || !this.summaryData.details) return 0
      var s = 0
      for (var i = 0; i < this.summaryData.details.length; i++) {
        var v = this.getActual(this.summaryData.details[i], empId)
        s += (v === "-" ? 0 : Number(v))
      }
      return s
    },
    getGrandAllocTotal() {
      if (!this.summaryData || !this.summaryData.details) return 0
      var s = 0
      for (var i = 0; i < this.summaryData.details.length; i++) {
        s += this.getAllocTotal(this.summaryData.details[i])
      }
      return s
    },
    getGrandActualTotal() {
      if (!this.summaryData || !this.summaryData.details) return 0
      var s = 0
      for (var i = 0; i < this.summaryData.details.length; i++) {
        s += Number(this.summaryData.details[i].total_actual) || 0
      }
      return s
    },
    doPrint() {
            uni.showToast({ title: "长按表格区域截图保存", icon: "none" })
                  if (!this.summaryData) return
      var table = document.getElementById("summary-table")
      if (!table) return
      var w = window.open("", "_blank")
      if (!w) return
      var t = this.summaryData.batch_name || "全品类汇总"
      w.document.write('<html><head><meta charset="UTF-8">')
      w.document.write('<html><head><meta charset="UTF-8"><style>' + PRINT_CSS + '</style></head><body>')
      w.document.write('<h2>' + t + '</h2>')
      w.document.write(table.outerHTML)
      w.document.write('</body></html>')
      w.document.close()
      setTimeout(function() { try { w.print(); w.close() } catch(e) {} }, 300)
          },
    downloadExcel() {
            if (!this.summaryData) return
      var table = document.getElementById("summary-table")
      if (!table) return
      var h = '<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40"><head><meta charset="UTF-8"><style>table{border-collapse:collapse}th,td{border:1px solid #000;padding:3px 4px;text-align:center;font-size:11px}th{background:#d9e1f2;font-weight:700}</style></head><body>'
      h += '<h2>' + (this.summaryData.batch_name || "全品类汇总") + '</h2>'
      h += '<p>报货: ' + (this.summaryData.arrival_time || "") + '</p>'
      h += table.outerHTML
      h += '</body></html>'
      var blob = new Blob([h], {type: "application/vnd.ms-excel"})
      var url = URL.createObjectURL(blob)
      var a = document.createElement("a")
      a.href = url; a.download = (this.summaryData.batch_name || "全品类汇总") + ".xls"
      document.body.appendChild(a); a.click(); document.body.removeChild(a)
      URL.revokeObjectURL(url)
    },
    // ===== Cargo Types =====
    async loadCargoTypes() {
      try { this.cargoTypes = await apiGet("/cargo-types") || [] } catch (e) { console.error(e) }
    },
    async addCargoType() {
      if (!this.cargoForm.name) return
      try {
        await apiPost("/cargo-types", this.cargoForm)
        this.cargoForm = { name: "", default_unit: "" }
        this.cargoMsg = "添加成功"
        await this.loadCargoTypes()
      } catch (e) { console.error(e) }
    },
    async deleteCargoType(id) {
      if (this.operating) return
      this.operating = true
      try {
        await apiDelete("/cargo-types/" + id)
        await this.loadCargoTypes()
      } catch (e) { console.error(e) }
      finally { this.operating = false }
    },
    // ===== Employees =====
    async addEmployee() {
      if (!this.empForm.display_name || !this.empForm.username) return
      try {
        await apiPost("/employees", this.empForm)
        this.empForm = { display_name: "", username: "", password: "" }
        this.empMsg = "添加成功"
        await this.loadEmployees()
      } catch (e) { console.error(e) }
    },
    async deleteEmployee(id) {
      if (this.operating) return
      this.operating = true
      try {
        await apiDelete("/employees/" + id)
        await this.loadEmployees()
      } catch (e) { console.error(e) }
      finally { this.operating = false }
    },
    // ===== Unit Types =====
    async loadUnitTypes() {
      try { this.unitTypes = await apiGet("/unit-types") || [] } catch (e) { console.error(e) }
    },
    async addUnitType() {
      if (!this.unitForm.name) return
      try {
        await apiPost("/unit-types", this.unitForm)
        this.unitForm = { name: "" }
        this.unitMsg = "添加成功"
        await this.loadUnitTypes()
      } catch (e) { console.error(e) }
    },
    editUnitType(ut) {
      var newName = prompt("输入新名称", ut.name)
      if (newName && newName !== ut.name) {
        var self = this
        apiPut("/unit-types/" + ut.id, { name: newName }).then(function() {
          self.loadUnitTypes()
        }).catch(function(e) { console.error(e) })
      }
    },
    async deleteUnitType(id) {
      if (this.operating) return
      this.operating = true
      try {
        await apiDelete("/unit-types/" + id)
        await this.loadUnitTypes()
      } catch (e) { console.error(e) }
      finally { this.operating = false }
    },
    // ===== Tooltip =====
    onCellEnter(event, item, emp, type) {
      var text = ""
      if (!item) return
      var itemName = item.name || ""
      var empName = emp ? (emp.name || "") : ""
      if (type === "alloc" && emp) {
        text = itemName + " " + empName + " 分货：" + (this.getItemQty(item, emp.id) || 0)
      } else if (type === "actual" && emp) {
        text = itemName + " " + empName + " 报货：" + (this.getItemActual(item, emp.id) || 0)
      } else if (type === "totalAlloc") {
        text = itemName + " 总分货：" + (this.getItemTotal(item) || 0)
      } else if (type === "totalActual") {
        text = itemName + " 总报货：" + (this.getItemActualTotal(item) || 0)
      }
      if (text) {
        this.tooltip.text = text
        this.tooltip.visible = true
      }
    },
    onCellLeave() {
      this.tooltip.visible = false
    },
    onRowEnter(item) {},
    onRowLeave() {}
  }
}
</script>
<style>
/* === Layout === */
.admin-layout { min-height: 100vh; background: #f5f6fa; }
.sidebar-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); z-index: 998; }
.sidebar { position: fixed; top: 0; left: 0; z-index: 999; width: 240px; height: 100vh; background: #1e2a3a; color: #ccc; display: flex; flex-direction: column; transform: translateX(-100%); transition: transform 0.25s ease; }
.sidebar.open { transform: translateX(0); box-shadow: 4px 0 20px rgba(0,0,0,0.3); }
.sidebar-header { padding: 16px 20px; font-size: 18px; font-weight: bold; color: #fff; border-bottom: 1px solid #2a3a4a; display: flex; justify-content: space-between; align-items: center; }
.sidebar-close { font-size: 20px; color: #888; cursor: pointer; padding: 4px; }
.sidebar-nav { flex: 1; padding: 8px 0; overflow-y: auto; }
.nav-item { display: flex; align-items: center; gap: 8px; padding: 12px 20px; color: #aaa; font-size: 14px; cursor: pointer; }
.nav-item.active { background: #3a4a5a; color: #fff; border-left: 3px solid #409eff; }
.nav-section-label { padding: 12px 20px 4px; font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 1px; border-top: 1px solid #2a3a4a; margin-top: 8px; }
.nav-icon { font-size: 16px; width: 22px; text-align: center; }
.sidebar-footer { padding: 14px 20px; border-top: 1px solid #2a3a4a; display: flex; justify-content: space-between; align-items: center; font-size: 13px; }
.sidebar-user { color: #aaa; }

/* === Main content === */
.main-content { padding: 12px; }
.mobile-header { display: flex; align-items: center; gap: 10px; padding: 8px 0 12px; border-bottom: 1px solid #eee; margin-bottom: 12px; position: relative; }
.mobile-header .hamburger { position: fixed; top: 10px; left: 10px; z-index: 997; width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; background: rgba(255,255,255,0.95); border-radius: 6px; box-shadow: 0 2px 8px rgba(0,0,0,0.12); color: #333; font-size: 22px; border: none; cursor: pointer; }
.mobile-title { font-size: 16px; font-weight: 600; color: #303133; padding-left: 44px; }
.page-title { font-size: 18px; font-weight: 600; color: #303133; margin-bottom: 12px; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.section-header .page-title { margin-bottom: 0; }

/* === Stats === */
.stats-row { display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }
.stat-card { flex: 1; min-width: calc(50% - 12px); background: #fff; border-radius: 8px; padding: 16px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.stat-num { display: block; font-size: 28px; font-weight: bold; color: #409eff; }
.stat-num.warning { color: #e6a23c; }
.stat-num.success { color: #67c23a; }
.stat-label { display: block; font-size: 13px; color: #999; margin-top: 4px; }
.stat-batch-name { display: block; font-size: 11px; color: #909399; margin-top: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 140px; margin-left: auto; margin-right: auto; }

/* === Card & list === */
.card { background: #fff; border-radius: 8px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 16px; }
.card-title { display: block; font-size: 16px; font-weight: 600; margin-bottom: 12px; }
.list-row { display: flex; padding: 10px 0; border-bottom: 1px solid #f0f0f0; }
.list-row.header { font-weight: 600; color: #666; font-size: 13px; }
.lcol-name { flex: 1; }
.lcol-time { width: 110px; text-align: center; font-size: 12px; }
.lcol-count { width: 50px; text-align: center; }
.success-msg { display: block; font-size: 13px; color: #67c23a; margin-bottom: 8px; }
.form-inline-card { display: flex; gap: 8px; align-items: center; margin-bottom: 12px; flex-wrap: wrap; background: #f8f9fc; border-radius: 6px; padding: 10px; }
.uni-input.inline { width: auto; flex: 1; min-width: 100px; padding: 10px 12px; border: 1px solid #dcdfe6; border-radius: 4px; font-size: 14px; box-sizing: border-box; min-height: 42px; line-height: 1.5; }

/* === Data table card (mobile version of HTML table) === */
.data-table-card { border: 1px solid #e0e0e0; border-radius: 4px; overflow: hidden; font-size: 13px; }
.dtr { display: flex; border-bottom: 1px solid #f0f0f0; }
.dtr:last-child { border-bottom: none; }
.dtr.dth { background: #fafafa; font-weight: 600; color: #666; }
.dtr:nth-child(even):not(.dth) { background: #fafafa; }
.dtc-id { width: 40px; padding: 10px 8px; text-align: center; color: #909399; }
.dtc-name { flex: 1; padding: 10px 8px; }
.dtc-unit { width: 100px; padding: 10px 8px; text-align: center; color: #606266; }
.dtc-action { width: 100px; padding: 8px; text-align: center; white-space: nowrap; }

/* === Batch select bar === */
.batch-select-bar { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; background: #fff; border-radius: 8px; padding: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 12px; }
.batch-picker { flex: 1; min-width: 160px; }
.batch-select-text { border: 1px solid #dcdfe6; border-radius: 4px; padding: 8px 12px; font-size: 14px; background: #fff; }

/* === Matrix table === */
.matrix-scroll { overflow-x: auto; background: #fff; border-radius: 8px; padding: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.matrix-toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.matrix-title { font-weight: 600; font-size: 14px; }
.matrix-hint { font-size: 11px; color: #909399; }
.matrix-wrap { min-width: 500px; border: 1px solid #000; }
.matrix-row { display: flex; border-bottom: 1px solid #000; }
.matrix-header { background: #d9e1f2; font-weight: 700; font-size: 12px; color: #333; }
.matrix-sub-header { background: #ecf5ff; font-size: 10px; color: #99c9ff; }
.matrix-data:nth-child(even) { background: #f8f9fc; }
.matrix-total { background: #eef1f8; font-weight: 600; border-top: 2px solid #000; }
.m-cell { padding: 3px 2px; border-right: 1px solid #000; text-align: center; font-size: 12px; white-space: nowrap; vertical-align: middle; }
.cell-name-w { min-width: 80px; text-align: left !important; padding-left: 6px !important; }
.cell-unit-w { min-width: 35px; }
.cell-emp-w { min-width: 40px; background: #ecf5ff; }
.cell-emp-header-w { min-width: 80px; background: #ecf5ff; color: #409eff; font-weight: 600; font-size: 12px; padding: 4px 4px !important; border-right: 1px solid #000; text-align: center; white-space: nowrap; }
.cell-total-w { min-width: 38px; background: #fdf6ec; color: #e6a23c; font-weight: 600; }
.cell-status-w { min-width: 40px; }
.cell-remark-w { min-width: 50px; font-size: 11px; }
.cell-action-w { min-width: 55px; }
.item-name-cell { cursor: pointer; color: #409eff; text-decoration: underline; }
.sub-label { font-size: 10px; }
.col-type-alloc { background-color: #fff8e1 !important; }
.col-type-actual { background-color: #e8f5e9 !important; }
.qty-input { width: 36px; padding: 2px 1px; border: 1px solid #dcdfe6; border-radius: 2px; font-size: 12px; text-align: center; }
.actual-qty { font-size: 11px; color: #67c23a; font-weight: 600; }
.badge { display: inline-block; padding: 2px 6px; border-radius: 10px; font-size: 10px; }
.badge-pending { background: #fdf6ec; color: #e6a23c; }
.badge-warn { background: #fef0f0; color: #f56c6c; }
.badge-ok { background: #f0f9eb; color: #67c23a; }

/* === Batch list cards === */
.batch-card-item { background: #fff; border-radius: 8px; padding: 14px; margin-bottom: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); border: 1px solid #eee; }
.bci-row { display: flex; align-items: center; gap: 12px; margin-bottom: 4px; }
.bci-row.sub { font-size: 12px; color: #909399; }
.bci-name { font-size: 16px; font-weight: 600; flex: 1; }
.bci-arrival { font-size: 13px; color: #606266; }
.bci-remark { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bci-date { color: #bbb; }
.bci-actions { margin-top: 8px; padding-top: 8px; border-top: 1px solid #f0f0f0; display: flex; gap: 8px; }

/* === Summary table === */
.summary-scroll { overflow-x: auto; background: #fff; border-radius: 8px; padding: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.summary-arrival { font-size: 15px; font-weight: 600; color: #303133; }
.summary-wrap { min-width: 500px; border: 1px solid #000; }
.s-row { display: flex; border-bottom: 1px solid #000; }
.s-header { background: #d9e1f2; font-weight: 700; font-size: 12px; color: #333; }
.s-subheader { background: #ecf5ff; font-size: 12px; color: #333; }
.s-data:nth-child(even) { background: #f8f9fc; }
.s-total { background: #eef1f8; font-weight: 600; border-top: 2px solid #000; }
.s-c { padding: 3px 2px; border-right: 1px solid #000; text-align: center; font-size: 12px; white-space: nowrap; }
.s-idx { min-width: 32px; width: 32px; }
.s-name { min-width: 70px; text-align: left !important; padding-left: 6px !important; }
.s-unit { min-width: 35px; font-size: 11px; color: #606266; }
.s-emp { min-width: 70px; background: #ecf5ff; padding: 4px 2px !important; }
.s-total-alloc { min-width: 42px; background: #fdf6ec; color: #e6a23c; border-left: 2px solid #000; }
.s-total-actual { min-width: 42px; background: #e8f5e9; color: #67c23a; }
.sub-alloc { color: #e6a23c; }
.sub-actual { color: #67c23a; }
.sub-div { color: #ccc; }
.cell-alloc { color: #e6a23c; font-weight: 500; font-size: 12px; }
.cell-actual { color: #67c23a; font-weight: 500; font-size: 12px; }
.cell-div { color: #ccc; font-size: 10px; }
.cell-alloc.total, .cell-actual.total { font-weight: 600; }

/* === Detail modal === */
.modal-header-bar { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.detail-info-row { display: flex; gap: 16px; font-size: 13px; color: #909399; margin-bottom: 12px; flex-wrap: wrap; }
.detail-table-wrap { border: 1px solid #000; border-radius: 4px; overflow: hidden; }
.detail-header-row, .detail-data-row, .detail-total-row { display: flex; border-bottom: 1px solid #000; }
.detail-total-row { background: #eef1f8; border-top: 2px solid #000; }
.dh-name { flex: 1; padding: 6px 8px; font-size: 13px; font-weight: 500; border-right: 1px solid #000; }
.dh-alloc { width: 80px; padding: 4px; text-align: center; border-right: 1px solid #000; }
.dh-actual { width: 80px; padding: 4px; text-align: center; }
.qty-input-detail { width: 60px; padding: 4px; border: 1px solid #dcdfe6; border-radius: 4px; font-size: 13px; text-align: center; }

/* === Tooltip === */
.matrix-tooltip { position: fixed; z-index: 10000; background: rgba(51,51,51,0.92); color: #fff; padding: 6px 10px; border-radius: 4px; font-size: 12px; pointer-events: none; white-space: nowrap; max-width: 280px; line-height: 1.5; }

/* === Modal === */
.modal-mask { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal-card { background: #fff; border-radius: 10px; padding: 24px; width: 90vw; max-width: 480px; max-height: 80vh; overflow-y: auto; }
.modal-wide { max-width: 600px; }
.modal-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; display: block; }
.modal-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 16px; }
.form-group { margin-bottom: 12px; }
.form-group label { display: block; font-size: 13px; color: #666; margin-bottom: 4px; }
.uni-input { width: 100%; padding: 10px 12px; border: 1px solid #dcdfe6; border-radius: 4px; font-size: 14px; margin-bottom: 12px; box-sizing: border-box; min-height: 42px; line-height: 1.5; }
.input-sm { padding: 6px 8px; font-size: 13px; }

/* === Empty states === */
.empty-hint { text-align: center; color: #909399; padding: 20px; font-size: 14px; }
.empty-hint-large { text-align: center; color: #909399; padding: 60px 20px; font-size: 15px; }

/* === Buttons === */
.btn { display: inline-block; padding: 6px 14px; border: 1px solid #dcdfe6; border-radius: 4px; background: #fff; font-size: 13px; cursor: pointer; text-align: center; }
.btn-primary { background: #409eff; border-color: #409eff; color: #fff; }
.btn-danger { background: #f56c6c; border-color: #f56c6c; color: #fff; }
.btn-sm { padding: 4px 10px; font-size: 12px; }
.btn-xs { padding: 2px 8px; font-size: 11px; }
.btn-excel { background: #67c23a; border-color: #67c23a; color: #fff; }

/* === Print === */
@media print { .no-print { display: none !important; } }
</style>
