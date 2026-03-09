<template>
  <header class="top-bar panel">
    <div class="top-row">
      <h1 class="brand">MyTube Radio</h1>
      <div class="search-group">
        <input
          :value="searchText"
          type="search"
          placeholder="Search local + YouTube"
          @input="$emit('search-text-change', $event.target.value)"
          @keydown.enter.prevent="$emit('search', searchText)"
        />
        <button type="button" @click="$emit('search', searchText)">Search</button>
      </div>
    </div>

    <form class="url-row" @submit.prevent="emitAddUrl">
      <input v-model="urlInput" type="url" placeholder="https://www.youtube.com/watch?v=..." required />
      <button type="submit">Add URL</button>
      <button type="button" class="alt" @click="emitPlayUrl">Play URL</button>
    </form>

    <div v-if="searchResults.length" class="search-results">
      <h2>YouTube Results</h2>
      <ul>
        <li v-for="item in searchResults" :key="item.id">
          <span>{{ item.title || item.source_url }}</span>
          <button type="button" @click="$emit('add-url', item.source_url)">Add</button>
          <button type="button" class="alt" @click="$emit('play-url', item.source_url)">Play</button>
        </li>
      </ul>
    </div>
  </header>
</template>

<script setup>
import { ref } from "vue";

defineProps({
  searchText: {
    type: String,
    default: "",
  },
  searchResults: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits(["add-url", "play-url", "search", "search-text-change"]);
const urlInput = ref("");

function emitAddUrl() {
  const url = urlInput.value.trim();
  if (!url) return;
  emit("add-url", url);
  urlInput.value = "";
}

function emitPlayUrl() {
  const url = urlInput.value.trim();
  if (!url) return;
  emit("play-url", url);
  urlInput.value = "";
}
</script>
