<template>
  <div class='admin-layout'>
    <!-- ============ 左侧菜单 ============ -->
    <aside class='sidebar'>
      <div class='sidebar-logo'> 分单系统</div>
      <nav class='sidebar-nav'>
        <a :class='{ active: currentPage==="dashboard" }' @click='currentPage="dashboard"'> 首页概览</a>
        <a :class='{ active: currentPage==="batches" }' @click='currentPage="batches"'> 分单管理</a>
        <a :class='{ active: currentPage==="summary" }' @click='openSummary'> 全品类汇总</a>
        <div style='margin:8px 18px;color:#666;font-size:12px;border-top:1px solid #333;padding-top:12px'>基础信息</div>
        <a :class='{ active: currentPage==="cargoTypes" }' @click='currentPage="cargoTypes"'> 货品种类</a>
        <a :class='{ active: currentPage==="employeeMgmt" }' @click='currentPage="employeeMgmt"'>👥 人员管理</a>
        <a :class='{ active: currentPage==="unitTypes" }' @click='currentPage="unitTypes"'> 单位管理</a>
      </nav>
      <div class='sidebar-footer'>
        <span>{{ user.display_name }}</span>
        <button class='btn btn-sm btn-danger' @click='logout'>退出</button>
      </div>
    </aside>
