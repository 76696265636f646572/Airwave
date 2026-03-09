<template>
  <section class="panel queue-panel">
    <h2>Queue</h2>
    <ul>
      <li v-for="item in queue" :key="item.id">
        <div class="text">
          <span class="title">#{{ item.queue_position }} {{ item.title || item.source_url }}</span>
          <span class="meta">{{ item.status }} · {{ item.channel || "unknown" }}</span>
        </div>
        <div class="actions">
          <button type="button" @click="$emit('reorder', { itemId: item.id, newPosition: Math.max(0, item.queue_position - 2) })">Up</button>
          <button type="button" @click="$emit('reorder', { itemId: item.id, newPosition: item.queue_position })">Down</button>
          <button type="button" class="alt" @click="$emit('remove', item.id)">Remove</button>
          <button
            type="button"
            class="alt"
            :disabled="!activePlaylistId"
            @click="$emit('save-to-playlist', item)"
          >
            Save
          </button>
        </div>
      </li>
    </ul>
  </section>
</template>

<script setup>
defineProps({
  queue: {
    type: Array,
    default: () => [],
  },
  activePlaylistId: {
    type: Number,
    default: null,
  },
});

defineEmits(["remove", "reorder", "save-to-playlist"]);
</script>
