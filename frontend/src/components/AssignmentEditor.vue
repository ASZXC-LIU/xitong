<template>
  <div class='assign-editor'>
    <div v-for='(a,i) in localAssignments' :key='i' class='assign-row'>
      <select v-model='a.user_id' @change='onChange'>
        <option value=''>-- 閫夋嫨鍛樺伐 --</option>
        <option v-for='e in availableEmployees(i)' :key='e.id' :value='e.id'>{{ e.display_name }}</option>
      </select>
      <input type='number' v-model.number='a.allocated_quantity' placeholder='鍒嗛厤鏁伴噺' step='any' min='0' @input='onChange' />
      <button class='btn btn-sm btn-danger' @click='removeRow(i)'>脳</button>
    </div>

    <button class='btn btn-sm btn-primary' @click='addRow' :disabled='allAssigned'>+ 娣诲姞鍛樺伐</button>

    <div style='margin-top:10px'>
      <button class='btn btn-primary btn-sm' @click='save' :disabled='saving'>
        {{ saving ? '淇濆瓨涓?..' : '馃捑 淇濆瓨鍒嗛厤' }}
      </button>
      <span v-if='msg' :style='msgStyle'>{{ msg }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue';

const props = defineProps({ item: Object, employees: Array });
const emit = defineEmits(['refresh']);
const API = 'http://localhost:5000/api';

const localAssignments = ref([]);
const saving = ref(false);
const msg = ref('');
const msgOk = ref(false);

const msgStyle = computed(() => ({
  color: msgOk.value ? '#67c23a' : '#f56c6c',
  marginLeft: '10px',
  fontSize: '13px',
}));

watch(() => props.item, (item) => {
  if (!item || !item.assignments) { localAssignments.value = []; return; }
  localAssignments.value = item.assignments.map(a => ({
    user_id: a.user_id,
    allocated_quantity: a.allocated_quantity,
  }));
}, { immediate: true });

const allAssigned = computed(() => {
  const assigned = localAssignments.value.filter(a => a.user_id).map(a => a.user_id);
  return props.employees?.every?.(e => assigned.includes(e.id)) ?? true;
});

function availableEmployees(currentIndex) {
  const assigned = localAssignments.value
    .filter((_, i) => i !== currentIndex)
    .map(a => a.user_id)
    .filter(Boolean);
  return (props.employees || []).filter(e => !assigned.includes(e.id));
}

function addRow() {
  localAssignments.value.push({ user_id: '', allocated_quantity: 0 });
}
function removeRow(i) {
  localAssignments.value.splice(i, 1);
  onChange();
}
function onChange() { msg.value = ''; }

async function save() {
  const valid = localAssignments.value.filter(a => a.user_id);
  if (valid.length === 0) { msg.value = '璇疯嚦灏戦€夋嫨涓€涓憳宸?; msgOk.value = false; return; }
  saving.value = true; msg.value = '';
  try {
    const res = await fetch(API + '/items/' + props.item.id + '/assignments', {
      method: 'PUT', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(valid),
    });
    if (res.ok) { msg.value = '淇濆瓨鎴愬姛'; msgOk.value = true; emit('refresh'); }
    else { msg.value = '淇濆瓨澶辫触'; msgOk.value = false; }
  } catch { msg.value = '缃戠粶閿欒'; msgOk.value = false; }
  finally { saving.value = false; setTimeout(() => msg.value = '', 2000); }
}
</script>

<style scoped>
.assign-editor { font-size: 13px; }
.assign-row { display: flex; gap: 6px; margin-bottom: 6px; align-items: center; }
.assign-row select { flex: 1; min-width: 0; }
.assign-row input { flex: 0.7; min-width: 60px; }
</style>
