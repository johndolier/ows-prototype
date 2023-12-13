
<template>
  <Card>
    <template #title>
      <PButton 
        v-if="content.is_html" 
        v-html="content.title" 
        :label="content.title" 
        link 
        @click="openLink(content.url)" 
      />
      <PButton 
        v-else 
        :label="content.title" 
        link 
        @click="openLink(content.url)"
      >
        {{ content.title }}
      </PButton>
    </template>
    <template #content>
      <div>
        <span class="w-full">
          <Tag 
            class="mx-2" 
            value="Web Document" 
            severity="warning"
          />
        </span>
      </div>
      <p ref="contentRef"
        v-if="content.is_html" 
        :class="showMore ? 'more-text' : 'less-text'"
        v-html="content.text"
      >
      </p>
      <p v-else class="overflow-y-auto w-full">
        {{ content.text }}
      </p>
      <PButton 
        v-if="contentOverflown"
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

  name: "WebDocumentComponent", 
  
  components: {
    Card, 
    Tag, 
  }, 
  props: {
    content: Object, 
  }, 

  data() {
    return {
      contentOverflown: false,
      showMore: false,
    }
  }, 

  methods: {
    openLink(link) {
      try {
        window.open(link);
      } catch (err) {
        console.log("error - could not open link");
        console.log(err);
      }
    }, 
    showMoreClicked() {
      this.showMore = !this.showMore;
    }
  }, 

  mounted() {
    // check if content text overflows the <p> element (with some margin)
      if (this.$refs.contentRef.scrollHeight > (this.$refs.contentRef.clientHeight + 5)) {
      this.contentOverflown = true;
    }
  }
}

</script>


<style scoped>

.less-text {
  width: 100%;
  overflow: hidden;
  line-height: 1em;
  height: 5em;
}

.more-text {
  width: 100%;
  overflow: hidden;
  line-height: 1em;
  height: auto;
}

</style>
