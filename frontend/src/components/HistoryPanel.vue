<template>
  <section class="panel history-panel">
    <h2>Play History</h2>
    <ul>
      <li v-for="item in history" :key="item.id">
        <span>{{ item.title || item.source_url }}</span>
        <span class="meta">{{ item.status }}</span>
      </li>
    </ul>
  </section>
</template>

<script setup>
defineProps({
  history: {
    type: Array,
    default: () => [],
  },
});
</script>
