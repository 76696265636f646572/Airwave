<template>
  <footer class="player-bar panel">
    <div class="info">
      <div class="title">{{ state.now_playing_title || "No active track" }}</div>
      <div class="meta">
        {{ state.mode?.toUpperCase() }}
        <span v-if="state.elapsed_seconds != null"> · {{ prettyTime(state.elapsed_seconds) }}</span>
        <span v-if="state.duration_seconds"> / {{ prettyTime(state.duration_seconds) }}</span>
      </div>
    </div>

    <div class="progress-wrap">
      <progress :max="100" :value="state.progress_percent || 0"></progress>
    </div>

    <audio controls :src="state.stream_url"></audio>

    <div class="actions">
      <a :href="state.stream_url" target="_blank" rel="noreferrer">Stream</a>
      <button type="button" @click="$emit('skip')">Skip</button>
    </div>
  </footer>
</template>

<script setup>
defineProps({
  state: {
    type: Object,
    required: true,
  },
});

defineEmits(["skip"]);

function prettyTime(value) {
  const totalSeconds = Math.max(0, Math.floor(value || 0));
  const mins = String(Math.floor(totalSeconds / 60)).padStart(2, "0");
  const secs = String(totalSeconds % 60).padStart(2, "0");
  return `${mins}:${secs}`;
}
</script>
