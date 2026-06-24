import { apiGet, apiPost, apiPut, apiDelete } from "./request"

// ===== 批次 =====
export function loadBatches() {
  return apiGet("/batches")
}

export function createBatch(data) {
  return apiPost("/batches", data)
}

export function updateBatch(id, data) {
  return apiPut("/batches/" + id, data)
}

export function deleteBatch(id) {
  return apiDelete("/batches/" + id)
}

// ===== 货品 =====
export function loadItems(batchId) {
  return apiGet("/batches/" + batchId + "/items")
}

export function addItem(batchId, data) {
  return apiPost("/batches/" + batchId + "/items", data)
}

export function deleteItem(id) {
  return apiDelete("/items/" + id)
}

export function saveAssignments(itemId, assignments) {
  return apiPut("/items/" + itemId + "/assignments", assignments)
}

// ===== 员工 =====
export function loadEmployees() {
  return apiGet("/employees")
}

export function createEmployee(data) {
  return apiPost("/employees", data)
}

export function updateEmployee(id, data) {
  return apiPut("/employees/" + id, data)
}

export function deleteEmployee(id) {
  return apiDelete("/employees/" + id)
}

// ===== 货品种类 =====
export function loadCargoTypes() {
  return apiGet("/cargo-types")
}

export function createCargoType(data) {
  return apiPost("/cargo-types", data)
}

// ===== 单位 =====
export function loadUnitTypes() {
  return apiGet("/unit-types")
}

export function createUnitType(data) {
  return apiPost("/unit-types", data)
}

// ===== 汇总 =====
export function loadSummary(batchId) {
  return apiGet("/batches/" + batchId + "/report")
}