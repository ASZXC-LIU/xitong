import { defineConfig } from "vite"
import uni from "@dcloudio/vite-plugin-uni"

function stripDevelopmentLoginForBuild(mode) {
  return {
    name: "strip-development-login-for-build",
    enforce: "pre",
    transform(code, id) {
      if (mode !== "production" || !id.endsWith("/src/pages/login/login.vue")) {
        return null
      }
      const stripped = code
        .replace(/<!-- DEV_LOGIN_START -->[\s\S]*?<!-- DEV_LOGIN_END -->/g, "")
        .replace(/\/\* DEV_LOGIN_START \*\/[\s\S]*?\/\* DEV_LOGIN_END \*\//g, "")
        .replace('<template v-if="!developmentLoginEnabled">', "<template>")
      return stripped === code ? null : { code: stripped, map: null }
    },
  }
}

export default defineConfig(({ mode }) => ({
  plugins: [stripDevelopmentLoginForBuild(mode), uni()],
  server: { port: 5173 }
}))
