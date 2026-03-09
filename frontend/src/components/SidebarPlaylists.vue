<template>
  <aside class="panel sidebar">
    <div class="sidebar-header">
      <h2>Playlists</h2>
      <form class="create-playlist" @submit.prevent="submitCreatePlaylist">
        <input v-model="newTitle" type="text" placeholder="New playlist" required />
        <button type="submit">Create</button>
      </form>
    </div>

    <ul class="playlist-list">
      <li
        v-for="playlist in playlists"
        :key="playlist.id"
        :class="{ active: playlist.id === activePlaylistId }"
      >
        <button type="button" class="playlist-select" @click="$emit('select-playlist', playlist.id)">
          <span class="title">{{ playlist.title }}</span>
          <span class="meta">{{ playlist.kind }} · {{ playlist.entry_count }}</span>
        </button>
        <button type="button" class="small" @click="$emit('queue-playlist', playlist.id)">Queue</button>
      </li>
    </ul>
  </aside>
</template>

<script setup>
import { ref } from "vue";

defineProps({
  playlists: {
    type: Array,
    default: () => [],
  },
  activePlaylistId: {
    type: Number,
    default: null,
  },
});

const emit = defineEmits(["create-playlist", "select-playlist", "queue-playlist"]);
const newTitle = ref("");

function submitCreatePlaylist() {
  const title = newTitle.value.trim();
  if (!title) return;
  emit("create-playlist", title);
  newTitle.value = "";
}
</script>
