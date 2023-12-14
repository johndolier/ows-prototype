<template>
  <Card>
    <template #title> 
      <div id ="titleElement" class="flex text-base">
        {{ content.title }}
      </div> 
    </template>
    <template #content>
      <div class="w-full">
        <PButton 
          class="p-1" 
          label="Publication" 
          severity="warning"
        />
        <!-- TODO style keywords - make them clickable -->
        <span 
          v-for="keyword in content.keywords" :key="keyword" 
          class="p-1"
          >
          <PButton :label="keyword" 
            class="tag-button"
          />
        </span>
        <span
          v-for="eoMission in eoMissions" :key="eoMission.short_name"
          class="p-1">
          <PButton 
            class="tag-button"
            :label="eoMission.short_name" 
            severity="danger" 
            v-tooltip="eoMission.full_name" 
          />
        </span>
        <span
          v-for="eoInstrument in eoInstruments" :key="eoInstrument.short_name" 
          class="p-1" >
          <PButton 
            class="tag-button"
            :label="eoInstrument.short_name" 
            severity="success" 
            v-tooltip="eoInstrument.full_name"
          />
        </span>
      </div>
      <p ref="abstractRef"
        align="left" 
        :class="{'more-text' : showMore, 'less-text' : (!showMore && normalStyle), 'no-text': (!showMore && !normalStyle)}"
      >
        {{ content.abstract }}
      </p>
      <PButton 
        v-if="abstractOverflown"
        :label="showMore ? 'Show less' : 'Show more'"
        link
        @click="showMoreClicked"
      />
    </template>
  </Card>
</template>


<script>

import Card from 'primevue/card';
// import Tag from 'primevue/tag';

export default {

  name: "PublicationComponent", 

  components: {
    Card, 
    // Tag, 
  }, 
  props: {
    content: Object, 
    normalStyle: Boolean, // this flag controls styling (can either be "normal" (true) or "small" style (false))
  }, 
  
  data() {
    return {
      showMore: false, 
      abstractOverflown: false, // is true when the abstract text overflows (computed at time of mount)
    }
  }, 

  computed: {
    eoMissions() {
      // returns a list of EO missions that are present in the STAC collection
      return this.content.eo_missions;
    }, 
    eoInstruments() {
      // returns a list of EO instruments that are present in the STAC collection
      return this.content.eo_instruments;
    }, 
  }, 

  methods: {
    showMoreClicked() {
      this.showMore = !this.showMore;
    }, 
  }, 

  mounted() {
    // check if description text overflows the <p> element (with some margin)
    if (this.$refs.abstractRef.scrollHeight > (this.$refs.abstractRef.clientHeight + 5)) {
      this.abstractOverflown = true;
    }
  }
}

</script>


<style scoped>

#titleElement {
  padding-left: 1rem;
  padding-top: 1rem;
  padding-bottom: 0;
}

.no-text {
  overflow: hidden;
  line-height: 1em;
  max-height: 3em;
}

.less-text {
  overflow: hidden;
  line-height: 1em;
  height: 8em;
}

.more-text {
  overflow: hidden;
  line-height: 1em;
  height: auto;
}

</style>
