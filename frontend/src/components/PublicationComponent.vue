<template>
  <div>
    <!-- This dialog displays EO Missions -->
    <Dialog v-if="eoMissionDetail"
      v-model:visible="showEOMissionDetail"
      modal
      :header="eoMissionDetail.full_name"
      :style="{width: '50rem'}"
      :breakpoints="{ '1199px': '75vw', '575px': '90vw' }"
    >
      <div class="flex">
        <p class="w-9 p-3">
          {{ eoMissionDetail.description }}
        </p>
        <PButton 
          class="w-2 m-5"
          severity="danger"
          label="Go To Mission Site"
          size="large"
          @click="openMissionSite(eoMissionDetail.mission_site)"
        />
      </div>
      <div>
        <b class="label vertical-align-baseline">Agencies:  </b>
      <PButton 
        class="vertical-align-baseline"
        :label="eoMissionDetail.agencies"
        severity="info"
      />
      </div>
    </Dialog>
    <!-- This dialog displays EO Instruments -->
    <Dialog v-if="eoInstrumentDetail"
      v-model:visible="showEOInstrumentDetail"
      modal
      :header="eoInstrumentDetail.full_name"
      :style="{width: '50rem'}"
      :breakpoints="{ '1199px': '75vw', '575px': '90vw' }"
    >
      <div>
        <p class="p-3">
          {{ eoInstrumentDetail.description }}
        </p>
      </div>
      <div class="p-1">
        <b class="label vertical-align-baseline">Type:  </b>
        <PButton
          class="p-2 vertical-align-baseline"
          :label="eoInstrumentDetail.instrument_type"
          severity="warning"
        />
      </div>
      <div class="p-1">
        <b class="label vertical-align-baseline">Technology:  </b>
        <PButton
          class="p-2 vertical-align-baseline"
          :label="eoInstrumentDetail.instrument_technology"
          severity="warning"
        />
      </div>
      <div class="p-1">
        <b class="label vertical-align-baseline">Waveband categories:  </b>
      <PButton 
        class="p-2 vertical-align-baseline"
        :label="eoInstrumentDetail.waveband_categories"
        severity="success"
      />
      </div>
      <div class="p-1">
        <b class="label vertical-align-baseline">Agencies:  </b>
      <PButton 
        class="p-2 vertical-align-baseline"
        :label="eoInstrumentDetail.agencies"
        severity="info"
      />
      </div>
    </Dialog>
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
          <span 
            v-for="keyword in content.keywords" :key="keyword" 
            class="p-1"
            >
            <PButton :label="keyword" 
              class="tag-button"
              @click="keywordClicked(keyword)"
            />
          </span>
          <span
            v-for="eoMission in eoMissions" :key="eoMission.short_name"
            class="p-1">
            <PButton 
              class="tag-button"
              :label="eoMission.short_name" 
              severity="danger" 
              @click="eoMissionDetailClicked(eoMission)"
            />
          </span>
          <span
            v-for="eoInstrument in eoInstruments" :key="eoInstrument.short_name" 
            class="p-1" >
            <PButton 
              class="tag-button"
              :label="eoInstrument.short_name" 
              severity="success" 
              @click="eoInstrumentDetailClicked(eoInstrument)"
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
  </div>
</template>


<script>

import Card from 'primevue/card';
import Dialog from 'primevue/dialog';


export default {

  name: "PublicationComponent", 

  components: {
    Card, 
    Dialog, 
  }, 
  props: {
    content: Object, 
    normalStyle: Boolean, // this flag controls styling (can either be "normal" (true) or "small" style (false))
  }, 

  emits: ['keywordClicked'],
  
  data() {
    return {
      showMore: false, 
      abstractOverflown: false, // is true when the abstract text overflows (computed at time of mount)
      eoMissionDetail: null, 
      eoInstrumentDetail: null,
      showEOMissionDetail: false,
      showEOInstrumentDetail: false, 
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
    keywordClicked(keyword) {
      // emit the keywordClicked event
      this.$emit('keywordClicked', keyword);
    }, 
    eoMissionDetailClicked(eoMission) {
      // open Dialog with EO mission details
      this.eoMissionDetail = eoMission;
      this.showEOMissionDetail = true;
    }, 
    eoInstrumentDetailClicked(eoInstrument) {
      // open Dialog with EO instrument details
      this.eoInstrumentDetail = eoInstrument;
      this.showEOInstrumentDetail = true;
    },
    openMissionSite(missionSite) {
      // open mission site in new tab
      window.open(missionSite);
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
