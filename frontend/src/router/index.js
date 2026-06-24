import { createRouter, createWebHashHistory } from "vue-router";
import Login from "../views/Login.vue";
import Admin from "../views/Admin.vue";
import Employee from "../views/Employee.vue";

const routes = [
  { path: "/", redirect: "/login" },
  { path: "/login", component: Login },
  { path: "/admin", component: Admin },
  { path: "/employee", component: Employee },
];

export default createRouter({ history: createWebHashHistory(), routes });
