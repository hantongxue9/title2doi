// 配置模板。部署时由 GitHub Actions 从 Secrets 注入生成 config.js。
// 本地开发：复制此文件为 config.js，填入你的 API Key。
// 用户也可在页面「高级设置」中覆盖这些配置。
window.T2D_CONFIG = {
  apiBase: 'https://api.deepseek.com/v1/chat/completions',
  apiKey: '',
  model: 'deepseek-v4-flash'
};
