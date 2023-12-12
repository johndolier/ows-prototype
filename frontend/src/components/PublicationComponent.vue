<template>
  <Card class="flex flex-column align-items-center sm:align-items-start gap-3">
    <template #title> 
      {{ content.title }}
    </template>
    <template #content>
      <div class="w-full">
        <span>
          <Tag 
            class="mx-2" 
            value="Publication" 
            severity="warning"
          />
          <!-- TODO style keywords - make them clickable -->
          <span 
            v-for="keyword in content.keywords" :key="keyword" 
            class="mx-1">
          <Tag :value="keyword" />
          </span>
          <!-- TODO display EO objects -->
        </span>
      </div>
      <p ref="abstractRef"
        :class="showMore ? 'more-text' : 'less-text'"
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
import Tag from 'primevue/tag';

export default {

  name: "PublicationComponent", 

  components: {
    Card, 
    Tag, 
  }, 
  props: {
    content: Object, 
  }, 
  
  data() {
    return {
      showMore: false, 
      abstractOverflown: false, // is true when the abstract text overflows (computed at time of mount)
    }
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
