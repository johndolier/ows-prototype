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
          @click="openSite(eoMissionDetail.mission_site)"
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
        <!--TODO make title link (details view)-->
        <div id="titleElement"
          class="flex text-base"
        >
          {{ content.title }}
        </div> 
      </template>
      <template #content>
        <div class="w-8 left-block">
          <div>
            <PButton 
              class="tag-button mx-1" 
              :label="content.stac_source.name" 
              severity="warning" 
              @click="openSite(content.stac_source.link)"
            />
            <PButton 
              class="tag-button mx-1" 
              label="External Links" 
              severity="info"
              @click="showExternalLinksClicked"
            />
            <OverlayPanel 
              ref="link_op"
            >
              <div v-for="link in content.links" :key="link">
                <div v-if="link.title">
                  <PButton 
                    class="tag-button" 
                    :label="link.title"
                    severity="info"
                    link
                    @click="openSite(link.href)"
                  />
                </div>
              </div>
            </OverlayPanel>
            <PButton 
              v-if="spatialExtentCoversGlobe"
              class="tag-button mx-1"
              label="Global"
              severity="secondary"
              v-tooltip="'STAC Collection covers the whole globe'"
              icon="pi pi-globe"
            />
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
          <div>
            <span 
              v-for="keyword in keywords" :key="keyword.id" 
              class="p-1">
              <PButton :label="keyword.name"
                class="tag-button"
                @click="keywordClicked(keyword)"
              />
            </span>
          </div>
          <p ref="descriptionRef"
            align="left" 
            :class="{'more-text' : showMore, 'less-text' : (!showMore && normalStyle), 'no-text': (!showMore && !normalStyle)}"
            v-html="content.description">
          </p>
          <PButton 
            v-if="descriptionOverflow"
            :label="showMore ? 'Show less' : 'Show more'"
            link
            @click="showMoreClicked"
          />
        </div>
        <div class="w-3 right-block">
          <div>
            <PButton v-if="normalStyle"
            label="Request STAC items" 
            @click="submitStacItemQuery" 
            icon="pi pi-cloud-download"
            icon-pos="right"
            severity="danger"
            :loading="stacItemsLoading"
            class="stac-button" 
          />
          <PButton v-if="normalStyle"
            label="STAC Notebook Download" 
            @click="downloadSTACNotebook" 
            icon="pi pi-download"
            icon-pos="left"
            severity="help" 
            class="stac-button" 
          />
          </div>
          <div>
            <PButton v-if="normalStyle"
            label="Show Spatial Extent"
            severity="info"
            icon="pi pi-map"
            icon-pos="right"
            class="stac-button"
            @click="showSpatialExtent"
          />
          <PButton v-if="tutorialLink && normalStyle" 
              class="stac-button"
              label="STAC Notebook Tutorial"
              icon-pos="left"
              icon="pi pi-star"
              severity="success"
              @click="openSite(tutorialLink)"
            />
          <img class="thumbnail-img" 
            :src="content.assets.thumbnail.href"
          />
          </div>


        </div>
        <div v-if="stacItemsPresent">
          <div class="overflow-hidden">
            <PButton 
                class="items-button"
                :label="'Show items (#' + currentlySelectedSTACItems.length + ')'" 
                @click="showItemsClick" 
                :icon="showItems ? 'pi pi-angle-double-down' : 'pi pi-angle-double-right' " 
              />
              <PButton
                class="map-button"
                label="Show STAC Items on Map"
                icon="pi pi-map"
                @click="showSTACItemsOnMap"
              />
          </div>
          <DataView 
            v-if="showItems" 
            :value="currentlySelectedSTACItems" 
            :layout="'grid'" 
            :rows="12"
            :paginator="currentlySelectedSTACItems.length > 12" 
            class="h-full"
          >
            <template #grid="slotProps">
              <div class="col-12 p-2 w-3">
                <div 
                  class="p-2"
                  :class="{'highlight-border' : (slotProps.data.id == currentlyHighlightedSTACItemID)}"
                  >
                  <img 
                    v-if="slotProps.data.img_link" 
                    class="stac-item-img" 
                    :src="slotProps.data.img_link"
                    v-tooltip="slotProps.data.id"
                    @click="onImageClick(slotProps.data)"
                    @dblclick="showSTACItemsOnMap"
                  />
                  <div v-else>
                    No image available
                  </div>
                </div>
              </div>
            </template>
          </DataView>
        </div>
      </template>
    </Card>
  </div>
</template>


<script>

import Card from 'primevue/card';
import DataView from 'primevue/dataview';
// import Tag from 'primevue/tag';
// import DynamicDialog from 'primevue/dynamicdialog';
import Dialog from 'primevue/dialog';

export default {

  name: "STACCollectionComponent", 

  components: {
    Card,
    // Tag,
    DataView, 
    // DynamicDialog, 
    Dialog, 
    }, 
  props: {
    content: Object, 
    globalSTACItems: Object, 
    normalStyle: Boolean, // this flag controls styling (can either be "normal" (true) or "small" style (false))
  }, 
  emits: [
    'submitStacItemQuery', 
    'downloadSTACNotebook', 
    'stacItemClicked', 
    'showSTACItemsOnMap', 
    'showSpatialExtent', 
    'keywordClicked', 
  ], 

  data() {
    return {
      showItems: false,
      showMore: false,
      descriptionOverflow: false, // is true when the description text overflows (computed at time of mount)
      showEOMissionDetail: false,
      showEOInstrumentDetail: false,
      eoMissionDetail: null, 
      eoInstrumentDetail: null, 
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
    keywords() {
      let keywords = [];
      for (const keywordNode of this.content.keywords) {
        keywords.push({
          'id': keywordNode.keyword._id, 
          'name': keywordNode.keyword.keyword_full, 
        })
      }
      return keywords;
    }, 
    stacItems() {
      // stacItems is a dictionary of STAC item requests performed on this STAC collection
      if (this.content._key in this.globalSTACItems) {
        return this.globalSTACItems[this.content._key]['requests'];
      }
      else {
        return null;
      }
    },
    stacItemsLoading() {
      // returns true if any STAC items are loading
      if (this.stacItems !== null) {
        for (const requestUID in this.stacItems) {
          if (this.stacItems[requestUID].loading) {
            return true;
          }
        }
      }
      return false;
    }, 
    currentlySelectedRequestUID() {
      // returns the current request item that is selected (if there is one)
      if (this.stacItems !== null) {
        for (const requestUID in this.stacItems) {
          if (this.stacItems[requestUID].selected) {
            return requestUID;
          }
        }
      }
      return null;
    }, 
    currentlySelectedRequest() {
      if (this.currentlySelectedRequestUID == null) {
        return null;
      }
      return this.stacItems[this.currentlySelectedRequestUID];
    }, 
    currentlyHighlightedSTACItemID() {
      // returns the ID of the currently highlighted STAC item
      if (this.currentlySelectedRequest !== null) {
        return this.currentlySelectedRequest.highlightID;
      }
      else {
        return null;
      }
    },
    currentlySelectedSTACItems() {
      // returns the STAC items that are currently selected
      // transforms the dictionary of STAC items into an array
      let stacItems = [];
      if (this.currentlySelectedRequest !== null) {
        for (const stacItemID in this.currentlySelectedRequest.stacItems) {
          stacItems.push(this.currentlySelectedRequest.stacItems[stacItemID]);
        }
      }
      return stacItems;
    }, 
    stacItemsPresent() {
      // returns true if there are any STAC items selected
      if (this.currentlySelectedRequest !== null) {
        return true;
      }
      else {
        return false;
      }
    }, 
    spatialExtentCoversGlobe() {
      // returns true if a bbox which covers whole globe is found in spatial extent variable of STAC collection
      for (const bbox of this.content.extent.spatial.bbox) {
        // check if bbox covers the whole map
        if (bbox.includes(180) && bbox.includes(-180) && bbox.includes(-90) && bbox.includes(90)) {
          return true;
        }
      }
      return false;
    },
    tutorialLink() {
      if (this.content.stac_source.name == 'Planetary Computer Data Catalog') {
        return 'https://planetarycomputer.microsoft.com/dataset/' + this.content._key + '#Example-Notebook'
      } else {
        return null;
      }
    }
  }, 

  methods: {
    keywordClicked(keyword) {
      // emit the keywordClicked event
      this.$emit('keywordClicked', keyword);
    },
    showMoreClicked() {
      this.showMore = !this.showMore;
    }, 
    submitStacItemQuery() {
      this.$emit('submitStacItemQuery', this.content._key);
    }, 
    showItemsClick() {
      this.showItems = !this.showItems;
    }, 
    downloadSTACNotebook() {
      this.$emit('downloadSTACNotebook', this.content._key);
    }, 
    onImageClick(stacItem) {
      const stacCollectionID = stacItem.collection;
      const stacItemID = stacItem.id;
      const requestUID = stacItem.requestUID;
      this.$emit('stacItemClicked', stacCollectionID, requestUID, stacItemID);
    },
    showSTACItemsOnMap() {
      const requestUID = this.currentlySelectedRequestUID;
      const stacCollectionID = this.content._key;
      this.$emit('showSTACItemsOnMap', stacCollectionID, requestUID);
    }, 
    showSpatialExtent() {
      // iterate over spatial extent bboxes and send event to MapView (show them in map)
      let filteredBBoxList = [];
      for (const bbox of this.content.extent.spatial.bbox) {
        if (bbox.includes(180) && bbox.includes(-180) && bbox.includes(-90) && bbox.includes(90)) {
          continue;
        }
        filteredBBoxList.push(bbox);
      }
      this.$emit('showSpatialExtent', filteredBBoxList);
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
    openSite(site) {
      // open mission site in new tab
      window.open(site);
    },
    showExternalLinksClicked(event) {
      this.$refs.link_op.toggle(event);
    }
  },

  mounted() {
    // check if description text overflows the <p> element (with some margin)
    if (this.$refs.descriptionRef && this.$refs.descriptionRef.scrollHeight > (this.$refs.descriptionRef.clientHeight + 5)) {
      this.descriptionOverflow = true;
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

.thumbnail-img {
    width: 100%;
    height: auto;
    box-shadow: 2px;
    border-radius: 0.25rem;
}

.stac-item-img {
    width: 100%;
    height: auto;
    border-radius: 0.1rem;
    display: inline-block;
}

.highlight-border {
  border-width: 2px !important;
  border-style: solid !important;
  border-color: #FF0000 !important;
}


.left-block {
  width: 67%;
  vertical-align: top;
  display: inline-block;
  margin-right:1rem !important;
}

.right-block {
  width: 33%;
  vertical-align: top;
  display: inline-block;
}

.no-text {
  overflow: hidden;
  line-height: 1em;
  max-height: 3em;
}
.less-text {
  overflow: hidden;
  line-height: 1em;
  max-height: 10em;
}

.more-text {
  overflow: hidden;
  line-height: 1em;
  height: auto;
}

.map-button {
  float: right;
  padding: 5px;
  margin: 3px;
}

.items-button {
  float: left;
  padding: 5px;
  margin: 3px;
}

.label {
  padding-top: 0.5rem;
  padding-bottom: 0.5rem;
  padding-right: 0.5rem;
}

.stac-button {
  width: 7rem;
  height: 3rem;
  padding: 0.2rem;
  margin: 0.2rem;
}


</style>
