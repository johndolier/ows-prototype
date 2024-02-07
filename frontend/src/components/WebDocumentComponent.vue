
<template>
<div>
  <!-- <OverlayPanel ref="op">
    <span
      v-for="location in content.locations" :key="location.name"
      class="p-1 float-left" >
      <PButton 
        class="tag-button"
        :label="location.name"
        severity="info"
        @click="locationClicked(location)"
      />
    </span>
  </OverlayPanel> -->
  <Card>
    <template #title>
      <PButton id="titleElement"
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
      <div v-if="hasGeodata">
        <PButton 
          class="tag-button m-1"
          label="Web Document"
          severity="warning"
        />
        <PButton 
          class=" tag-button m-1"
          :label="location.name"
          icon="pi pi-compass"
          severity=""
        />
        <PButton 
          class=" tag-button m-1"
          label="Show On Map"
          icon="pi pi-map"
          severity="success"
          @click="showGeodata"
        />
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
</div>
</template>

<script>

import Card from 'primevue/card';
// import Tag from 'primevue/tag';

export default {

  name: "WebDocumentComponent", 

  emits: [
    "showGeodata"
  ], 
  
  components: {
    Card, 
    // Tag, 
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

  computed: {
    hasGeodata() {
      // console.log(this.content.locations);
      if (this.content.locations.length > 0) {
        return true;
      }
      return false;
    }, 
    location() {
      if (this.hasGeodata) {
        return this.content.locations[0];
      }
      return null;
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
    }, 
    showGeodata() {
      this.$emit('showGeodata', this.location);
    }, 
    showLocations(event) {
      // disabled
      // this.$refs.op.toggle(event);
      console.log(event);
    }, 
  }, 

  mounted() {
    // check if content text overflows the <p> element (with some margin)
    if (this.$refs.contentRef && this.$refs.contentRef.scrollHeight > (this.$refs.contentRef.clientHeight + 5)) {
      this.contentOverflown = true;
    }
    // console.log(this.content);
  }
}

</script>


<style scoped>

#titleElement {
  font-size: 0.8em;
  padding-top: 1rem;
  padding-left: 1rem;
  float: left;
}

.less-text {
  width: 100%;
  overflow: hidden;
  line-height: 1em;
  max-height: 5em;
}

.more-text {
  width: 100%;
  overflow: hidden;
  line-height: 1em;
  height: auto;
}

</style>
