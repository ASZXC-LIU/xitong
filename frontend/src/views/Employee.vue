
<template>
  <div class="emp-page">
    <header class="emp-header">
      <button v-if="selectedBatchId" class="btn btn-sm" @click="backToBatches">返回</button>
      <h2>{{ selectedBatchId ? batchName : '我的工单' }}</h2>
      <div>
        <span class="emp-user">{{ user.display_name }}</span>
        <button class="btn btn-sm btn-danger" @click="logout">退出</button>
      </div>
    </header>

    <div v-if="!selectedBatchId">
      <div v-if="myBatches.length === 0" class="empty-state">
        <div class="empty-icon">暂无工单</div>
        <p>您还没有被分货货品</p>
      </div>
      <div v-for="b in myBatches" :key="b.id" class="batch-card" @click="selectBatch(b)">
        <div class="batch-card-name">{{ b.name }}</div>
        <div class="batch-card-meta">
          <span>到货: {{ b.arrival_time }}</span>
          <span>货品: {{ b.item_count }} 种</span>
        </div>
        <div class="batch-card-date">{{ b.created_at?.slice(0,10) }}</div>
      </div>
    </div>

    <div v-if="selectedBatchId" class="table-wrap">
      <div class="table-toolbar">
        <span class="table-info">{{ batchName }} - 共 {{ myItems.length }} 种货品</span>
      </div>
      <div v-if="myItems.length === 0" class="empty-state">
        <div class="empty-icon">暂无货品</div>
      </div>
      <div v-else class="matrix-table-wrap">
        <table class="emp-table">
          <thead>
            <tr>
              <th>货品名称</th>
              <th>单位</th>
              <th>分货数量</th>
              <th>报货数量</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in myItems" :key="item.item_id">
              <td class="col-name">{{ item.item_name }}</td>
              <td class="col-unit">{{ item.item_unit }}</td>
              <td class="col-alloc">{{ item.allocated_quantity }}</td>
              <td class="col-qty">
                <input type="number" v-model.number="item.editQty"
                       step="any" min="0" class="qty-input"
                       @blur="submitItem(item)"
                       @keyup.enter="submitItem(item)"
                       :placeholder="item.item_unit" />
              </td>
              <td class="col-status">
                <span :class="'tag ' + statusTag(item)">{{ itemStatusText(item) }}</span>
              </td>
              <td class="col-action">
                <button class="btn btn-sm btn-primary" @click="submitItem(item)" :disabled="item.saving">
                  {{ item.saving ? '...' : '保存' }}
                </button>
                <span v-if="item.saved" class="save-ok">✓</span>
                <span v-if="item.error" class="save-err">!</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-if="saveMsg" :class="'save-toast ' + (saveOk ? 'toast-ok' : 'toast-err')">{{ saveMsg }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
const router = useRouter();

const API = "http://localhost:5000/api";
const user = ref(JSON.parse(localStorage.getItem("user") || "{}"));
const myBatches = ref([]);
const myItems = ref([]);
const selectedBatchId = ref(null);
const batchName = ref("");
const saveMsg = ref("");
const saveOk = ref(false);

function statusTag(item) {
  if (item.actual_quantity != null && Number(item.actual_quantity) > 0) return "tag-success";
  if (item.allocated_quantity > 0) return "tag-warning";
  return "tag-default";
}

function itemStatusText(item) {
  if (item.actual_quantity != null && Number(item.actual_quantity) > 0) return "已报货";
  if (item.allocated_quantity > 0) return "待报货";
  return "未分配";
}

async function loadMyBatches() {
  try {
    const res = await fetch(API + "/employee/my-batches?user_id=" + user.value.id);
    myBatches.value = await res.json();
  } catch (e) {
    console.error("loadMyBatches", e);
  }
}

async function selectBatch(b) {
  selectedBatchId.value = b.id;
  batchName.value = b.name;
  try {
    const res = await fetch(API + "/employee/my-items?user_id=" + user.value.id + "&batch_id=" + b.id);
    const data = await res.json();
    myItems.value = data.map(item => ({
      ...item,
      editQty: item.actual_quantity ?? item.allocated_quantity,
      saving: false,
      saved: false,
      error: "",
    }));
  } catch (e) {
    console.error("selectBatch", e);
  }
}

function backToBatches() {
  selectedBatchId.value = null;
  myItems.value = [];
  batchName.value = "";
}

async function submitItem(item) {
  if (item.saving) return;
  if (item._timeout) clearTimeout(item._timeout);
  item.saving = true;
  item.saved = false;
  item.error = "";
  try {
    const payload = {
      assignment_id: item.assignment_id,
      batch_item_id: item.item_id,
      user_id: user.value.id,
      actual_quantity: Number(item.editQty) || 0,
    };
    const res = await fetch(API + "/employee/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (res.ok) {
      const data = await res.json();
      item.assignment_id = data.assignment_id || item.assignment_id;
      item.saved = true;
      item.actual_quantity = Number(item.editQty) || 0;
      saveMsg.value = "\u5df2\u4fdd\u5b58";
      saveOk.value = true;
      setTimeout(() => { saveMsg.value = ""; }, 2000);
      item._timeout = setTimeout(() => { item.saved = false; }, 2000);
    } else {
      const err = await res.json();
      item.error = err.error || "\u4fdd\u5b58\u5931\u8d25";
      saveMsg.value = item.error;
      saveOk.value = false;
    }
  } catch {
    item.error = "\u7f51\u7edc\u9519\u8bef";
    saveMsg.value = item.error;
    saveOk.value = false;
  } finally {
    item.saving = false;
  }
}

function logout() {
  localStorage.removeItem("user");
  router.push("/login");
}

onMounted(() => {
  if (!user.value.id) { router.push("/login"); return; }
  loadMyBatches();
});

// Auto-refresh when page gets focus
window.addEventListener("focus", () => {
  if (!selectedBatchId.value) {
    loadMyBatches();
  } else {
    selectBatch({ id: selectedBatchId.value, name: batchName.value });
  }
});
</script>

<style scoped>
.emp-page { max-width: 800px; margin: 0 auto; padding: 12px; font-size: 14px; }
.emp-header { display: flex; align-items: center; gap: 8px; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid #eee; flex-wrap: wrap; }
.emp-header h2 { flex: 1; font-size: 18px; margin: 0; }
.emp-user { font-size: 13px; color: #606266; margin-right: 8px; }
.empty-state { text-align: center; padding: 40px 20px; color: #909399; }
.empty-icon { font-size: 18px; margin-bottom: 8px; }

.batch-card { background: #fff; border-radius: 10px; padding: 14px 16px; margin-bottom: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); border: 1px solid #eee; cursor: pointer; transition: 0.2s; }
.batch-card:active { transform: scale(0.98); background: #f5f7fa; }
.batch-card-name { font-size: 16px; font-weight: 600; color: #303133; margin-bottom: 6px; }
.batch-card-meta { display: flex; gap: 16px; font-size: 13px; color: #606266; }
.batch-card-date { font-size: 12px; color: #bbb; margin-top: 6px; }

.table-wrap { background: #fff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); overflow: hidden; }
.table-toolbar { padding: 12px 14px; border-bottom: 1px solid #eee; background: #fafafa; }
.table-info { font-size: 13px; color: #606266; }
.matrix-table-wrap { overflow-x: auto; }
.emp-table { width: 100%; border-collapse: collapse; font-size: 13px; min-width: 500px; }
.emp-table th { background: #d9e1f2; font-weight: 700; font-size: 12px; color: #333; padding: 8px 6px; border-bottom: 2px solid #000; text-align: center; white-space: nowrap; }
.emp-table td { padding: 6px 4px; border-bottom: 1px solid #e0e0e0; text-align: center; vertical-align: middle; }
.emp-table tbody tr:nth-child(even) { background: #f8f9fc; }
.emp-table tbody tr:hover { background: #ecf5ff; }
.col-name { text-align: left !important; font-weight: 500; padding-left: 10px !important; white-space: nowrap; }
.col-unit { color: #909399; font-size: 12px; }
.col-alloc { color: #e6a23c; font-weight: 500; }
.col-qty { min-width: 100px; }
.qty-input { width: 80px; padding: 6px 8px; border: 1px solid #dcdfe6; border-radius: 4px; font-size: 13px; text-align: center; }
.qty-input:focus { border-color: #409eff; box-shadow: 0 0 0 2px rgba(64,158,255,0.2); outline: none; }
.col-action { white-space: nowrap; }
.save-ok { color: #67c23a; font-weight: bold; margin-left: 4px; }
.save-err { color: #f56c6c; font-weight: bold; margin-left: 4px; }
.tag { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px; }
.tag-success { background: #f0f9eb; color: #67c23a; }
.tag-warning { background: #fdf6ec; color: #e6a23c; }
.tag-default { background: #f0f2f5; color: #909399; }
.save-toast { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); padding: 10px 20px; border-radius: 6px; font-size: 14px; z-index: 1000; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
.toast-ok { background: #f0f9eb; color: #67c23a; border: 1px solid #c2e7b0; }
.toast-err { background: #fef0f0; color: #f56c6c; border: 1px solid #fbc4c4; }
.btn { display: inline-block; padding: 6px 14px; border: 1px solid #dcdfe6; border-radius: 4px; background: #fff; cursor: pointer; font-size: 13px; }
.btn-primary { background: #409eff; border-color: #409eff; color: #fff; }
.btn-primary:disabled { background: #a0cfff; border-color: #a0cfff; cursor: not-allowed; }
.btn-danger { background: #f56c6c; border-color: #f56c6c; color: #fff; }
.btn-sm { padding: 4px 10px; font-size: 12px; }
@media (max-width: 600px) {
  .emp-table { font-size: 12px; min-width: 400px; }
  .emp-table th, .emp-table td { padding: 4px 2px; }
  .qty-input { width: 60px; padding: 4px 6px; font-size: 12px; }
  .col-name { min-width: 60px; }
}
</style>
