<script setup lang="ts">
withDefaults(defineProps<{ name: string; size?: number }>(), { size: 18 })
const paths: Record<string, string> = {
  voice: 'M4 10v4M8 6v12M12 3v18M16 6v12M20 10v4',
  panel: 'M3 3h18v18H3zM9 3v18',
  menu: 'M4 6h16M4 12h16M4 18h16',
  chat: 'M21 11.5a8.5 8.5 0 0 1-8.5 8.5H4l-3 2 1.7-5.2A8.5 8.5 0 1 1 21 11.5Z',
  new: 'M12 5H4v16h16v-8M15 3h6v6M21 3l-9 9',
  data: 'M4 5h16v15H4zM4 10h16M4 15h16M9 5v15',
  upload: 'M12 16V3M7 8l5-5 5 5M4 16v5h16v-5',
  plus: 'M12 5v14M5 12h14',
  chart: 'M4 3v18h17M8 16v-4M13 16V7M18 16v-7',
  search: 'M21 21l-5-5M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0',
  calculator: 'M5 2h14v20H5zM8 6h8M8 11h1M15 11h1M8 15h1M15 15h1M8 18h1M15 18h1',
  settings: 'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8M4 12H2M22 12h-2M12 4V2M12 22v-2M6.3 6.3 4.9 4.9M19.1 19.1l-1.4-1.4M6.3 17.7l-1.4 1.4M19.1 4.9l-1.4 1.4',
  arrow: 'M12 19V5M6 11l6-6 6 6',
  close: 'M6 6l12 12M6 18 18 6',
  export: 'M12 3v12M7 10l5 5 5-5M4 16v5h16v-5',
  external: 'M14 3h7v7M21 3 11 13M10 3H3v18h18v-7',
  check: 'M5 12l4 4L19 6',
  shield: 'M12 2 3 6v6c0 5 9 10 9 10s9-5 9-10V6l-9-4ZM8 12l3 3 5-6',
  chevron: 'M9 5l7 7-7 7',
  file: 'M14 2H4v20h16V8l-6-6ZM14 2v6h6M8 13h8M8 17h6',
}
</script>
<template><svg :width="size" :height="size" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path :d="paths[name] || paths.chat" /></svg></template>
