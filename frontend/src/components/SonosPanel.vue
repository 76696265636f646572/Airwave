<template>
  <aside class="panel sonos-panel">
    <div class="header-row">
      <h2>Sonos</h2>
      <button type="button" @click="$emit('refresh')">Refresh</button>
    </div>

    <ul>
      <li v-for="speaker in speakers" :key="speaker.uid">
        <div class="speaker-main">
          <div>
            <div class="title">{{ speaker.name }}</div>
            <div class="meta">{{ speaker.ip }}</div>
          </div>
          <button type="button" @click="$emit('play', speaker.ip)">Play</button>
        </div>

        <div class="group-row">
          <select v-model="groupTargets[speaker.ip]">
            <option :value="speaker.ip">Group target</option>
            <option
              v-for="coordinator in coordinators(speaker.ip)"
              :key="coordinator.ip"
              :value="coordinator.ip"
            >
              {{ coordinator.name }}
            </option>
          </select>
          <button
            type="button"
            @click="$emit('group', { coordinatorIp: groupTargets[speaker.ip], memberIp: speaker.ip })"
          >
            Group
          </button>
          <button type="button" class="alt" @click="$emit('ungroup', speaker.ip)">Ungroup</button>
        </div>

        <label class="volume-row">
          <span>Volume</span>
          <input
            type="range"
            min="0"
            max="100"
            :value="speaker.volume ?? 0"
            @change="$emit('set-volume', { ip: speaker.ip, volume: Number($event.target.value) })"
          />
          <span>{{ speaker.volume ?? 0 }}</span>
        </label>
      </li>
    </ul>
  </aside>
</template>

<script setup>
import { reactive } from "vue";

const props = defineProps({
  speakers: {
    type: Array,
    default: () => [],
  },
});

defineEmits(["refresh", "play", "group", "ungroup", "set-volume"]);

const groupTargets = reactive({});

function coordinators(currentIp) {
  return props.speakers.filter((speaker) => speaker.ip !== currentIp && speaker.is_coordinator);
}
</script>
