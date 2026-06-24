
<template>
  <div class="emp-container">
    <!-- 头部 -->
    <header class="emp-header">
      <button v-if="selectedBatchId" class="btn btn-sm" @click="backToBatches">返回</button>
      <h2>{{ selectedBatchId ? batchName : '我的工单' }}</h2>
      <div>
        <span class="emp-user">{{ user.display_name }}</span>
        <button class="btn btn-sm btn-danger" @click="logout">退出</button>
      </div>
    </header>

    <!-- 批次列表 -->
    <div v-if="!selectedBatchId">
      <div v-if="myBatches.length === 0" class="empty-state">
        <div class="empty-icon">暂无工单</div>
        <p>您还没有被分配货品</p>
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

    <!-- 货品列表 (选中批次后) -->
    <div v-if="selectedBatchId">
      <div v-if="myItems.length === 0" class="empty-state">
        <div class="empty-icon">暂无货品</div>
      </div>
      <div v-for="item in myItems" :key="item.item_id" class="item-card">
        <div class="item-card-header">
          <strong class="item-name">{{ item.item_name }}</strong>
          <span class="item-unit">{{ item.item_unit }}</span>
          <span :class="'tag ' + statusTag(item)">{{ itemStatusText(item) }}</span>
        </div>
        <div class="item-card-body">
          <div class="info-row">
            <span class="info-label">分配数量</span>
            <span class="info-value">{{ item.allocated_quantity }} {{ item.item_unit }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">报货数量</span>
            <input type="number" v-model.number="item.editQty" 
                   step="any" min="0" class="qty-input"
                   @blur="submitItem(item)"
                   @keyup.enter="submitItem(item)"
                   :placeholder="'输入报货数量 (' + item.item_unit + ')'" />
          </div>
          <div v-if="item.remark" class="info-row">
            <span class="info-label">备注</span>
            <span class="info-value" style="color:#909399">{{ item.remark }}</span>
          </div>
        </div>
        <div class="item-card-footer">
          <button class="btn btn-primary btn-sm" @click="submitItem(item)" :disabled="item.saving">
            {{ item.saving ? '保存中...' : '保存' }}
          </button>
          <span v-if="item.saved" class="save-success">已保存</span>
          <span v-if="item.error" class="save-error">{{ item.error }}</span>
        </div>
      </div>
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
      item._timeout = setTimeout(() => { item.saved = false; }, 2000);
    } else {
      const err = await res.json();
      item.error = err.error || "保存失败";
    }
  } catch {
    item.error = "网络错误";
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
.emp-container { max-width: 600px; margin: 0 auto; padding: 12px; font-size: 14px; }
.emp-header { display: flex; align-items: center; gap: 8px; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid #eee; }
.emp-header h2 { flex: 1; font-size: 18px; margin: 0; }
.emp-user { font-size: 13px; color: #606266; margin-right: 8px; }

/* 空状态 */
.empty-state { text-align: center; padding: 40px 20px; color: #909399; }
.empty-icon { font-size: 18px; margin-bottom: 8px; }

/* 批次卡片 */
.batch-card { background: #fff; border-radius: 10px; padding: 14px 16px; margin-bottom: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); border: 1px solid #eee; cursor: pointer; transition: 0.2s; }
.batch-card:active { transform: scale(0.98); background: #f5f7fa; }
.batch-card-name { font-size: 16px; font-weight: 600; color: #303133; margin-bottom: 6px; }
.batch-card-meta { display: flex; gap: 16px; font-size: 13px; color: #606266; }
.batch-card-date { font-size: 12px; color: #bbb; margin-top: 6px; }

/* 货品卡片 */
.item-card { background: #fff; border-radius: 10px; padding: 14px 16px; margin-bottom: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); border: 1px solid #eee; }
.item-card-header { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; padding-bottom: 10px; border-bottom: 1px solid #f0f0f0; }
.item-name { font-size: 16px; flex: 1; }
.item-unit { font-size: 12px; color: #909399; }
.item-card-body { margin-bottom: 12px; }
.info-row { display: flex; align-items: center; padding: 6px 0; gap: 8px; }
.info-label { font-size: 13px; color: #909399; min-width: 70px; }
.info-value { font-size: 14px; font-weight: 500; color: #303133; }
.qty-input { flex: 1; max-width: 180px; padding: 8px 10px; border: 1px solid #dcdfe6; border-radius: 6px; font-size: 14px; outline: none; }
.qty-input:focus { border-color: #409eff; box-shadow: 0 0 0 2px rgba(64,158,255,0.2); }
.item-card-footer { display: flex; align-items: center; gap: 10px; padding-top: 10px; border-top: 1px solid #f0f0f0; }
.save-success { font-size: 13px; color: #67c23a; }
.save-error { font-size: 13px; color: #f56c6c; }

/* 状态标签 */
.tag { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px; }
.tag-success { background: #f0f9eb; color: #67c23a; }
.tag-warning { background: #fdf6ec; color: #e6a23c; }
.tag-default { background: #f0f2f5; color: #909399; }

.btn { display: inline-block; padding: 6px 14px; border: 1px solid #dcdfe6; border-radius: 4px; background: #fff; cursor: pointer; font-size: 13px; transition: 0.2s; }
.btn:hover { border-color: #409eff; color: #409eff; }
.btn-primary { background: #409eff; border-color: #409eff; color: #fff; }
.btn-primary:hover { background: #66b1ff; border-color: #66b1ff; color: #fff; }
.btn-danger { background: #f56c6c; border-color: #f56c6c; color: #fff; }
.btn-danger:hover { background: #f78989; border-color: #f78989; color: #fff; }
.btn-sm { padding: 4px 10px; font-size: 12px; }
</style>
