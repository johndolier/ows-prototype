<template>
  <div class="home h-screen w-screen">
    <PToast 
      position="top-center" 
      group="tc" 
    />
    <PToast 
      position="top-left" 
      group="tl" 
    />
    <ConfirmDialog />
    <!-- Siebar component for advanced query and filtering documents -->
    <PSidebar 
      v-model:visible="showAdvancedSearch" 
      position="left" 
      :modal="false"
    >
      <h2>
        Advanced Search
      </h2>
      <div class="advanced-search-element">
        <p 
          align="left" 
          class="advanced-search-header"
        >
          Time Filter
        </p>
        <VueDatePicker 
          v-model="timeRangeFilter" 
          range 
          :partial-range="false" 
          class="advanced-search-body"
        />
        <PButton 
          v-if="timeSelected"
          class="my-2 center-button"
          severity="danger"
          icon="pi pi-ban"
          label="Clear Time Selection"
          @click="clearTimeSelection" 
        />
      </div>
      <PButton 
        v-if="!showStartScreen" 
        class="my-2" 
        severity="info" 
        label="SHOW GEOTWEETS (DEBUG)"
        @click="requestGeotweets" 
      />
    </PSidebar>

    <div v-if="showStartScreen">
      <div 
        id="appHeader" 
        class="text-xl font-bold py-4 bg-primary">
        <header>
          OpenSearch@DLR Prototype
        </header>
      </div>
      <!-- START SCREEN -->
      <SearchHeaderComponent 
        class="center"
        :queryIsLoading="queryIsLoading" 
        :showAdvancedSearch="showAdvancedSearch" 
        startText="Start your search here..." 
        @submitQuery="this.submitQuery" 
        @advancedSearchClick="this.advancedSearchClick"
      />
    </div>
    <div v-else>
      <!-- "NORMAL" SCREEN -->
      <SearchHeaderComponent 
        id="searchHeader" 
        class="center-x surface-ground z-1"
        :queryIsLoading="queryIsLoading" 
        :showAdvancedSearch="showAdvancedSearch"
        @submitQuery="this.submitQuery" 
        @advancedSearchClick="this.advancedSearchClick"
      />
      <div id="documentBody" class=" surface-ground flex">
        <div class="column">
          <!-- left column -->
          <DocumentListComponent
            id="documentListComponent"
            :documents="documents" 
            :stacItems="stacItems" 
            initial-document-type="Web Documents"
            :show-top-results-only="false"
            :search-query="lastUserQuery"
            @submitStacItemQuery="submitStacItemQuery" 
            @downloadSTACNotebook="downloadSTACNotebook"
          />
        </div>
        <div class="column">
          <!-- right column -->
          <MapComponent 
            id="mapComponent" 
            ref="mapRef"
            :documents="documents" 
            :stacItems="stacItems" 
            :initial-focus-list="initialFocusList"
            :show-map="showMap"
            @show-map-clicked="showMapClicked"
          />
          <div v-if="showTopSTACResults">
            <DocumentListComponent
              class="topResultListComponent"
              :documents="documents" 
              :stacItems="stacItems" 
              initial-document-type="STAC Collections"
              :is-top-results-list="true"
              :search-query="lastUserQuery"
              @submitStacItemQuery="submitStacItemQuery" 
              @downloadSTACNotebook="downloadSTACNotebook"
              @close-document-list="closeDocumentList"
           />
          </div>
          <div v-if="showTopPublicationResults">
            <DocumentListComponent
              class="topResultListComponent"
              :documents="documents" 
              :stacItems="stacItems" 
              initial-document-type="Publications"
              :is-top-results-list="true"
              :search-query="lastUserQuery"
              @submitStacItemQuery="submitStacItemQuery" 
              @downloadSTACNotebook="downloadSTACNotebook"
              @close-document-list="closeDocumentList"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
// @ is an alias to /src
import MapComponent from '@/components/MapComponent.vue';
import DocumentListComponent from '@/components/DocumentListComponent.vue';
import SearchHeaderComponent from '@/components/SearchHeaderComponent.vue';

import axios from 'axios';

import { v4 as get_uid } from 'uuid';

export default {

  name: 'HomeView',

  components: {
    MapComponent,
    DocumentListComponent, 
    SearchHeaderComponent, 
  }, 
  // inject helper functions
  inject: ['Utils'], 
  data () {
    return {
      // main variable to hold response from server
      // gets refreshed for each new user query 
      documents: {
        'publications': [],  
        'stac_collections': [], 
        'web_documents': [],
      }, 
      // stacItems contain all the fetched STAC items frmo this user session
      stacItems: {}, 
      // keywords: [], 

      // last user query
      lastUserQuery: null, 

      // UI STATE VARIABLES
      showStartScreen: true, 
      // user input
      queryIsLoading: false,
      // advanced search
      showAdvancedSearch: false, 
      // control which elements are shown
      showMap: true, 
      showTopSTACResults: true, 
      showTopPublicationResults: true, 

      // FILTERS
      timeRangeFilter: [], 
      initialFocusList: null, 
      // data types to include in DocumentListView (for now they are redundant and not used -> always true)
      selectPublications: true, 
      selectSTACCollections: true, 
      selectWebDocuments: true, 
    }
  }, 

  async created() {
    // currently keywords are not used ()
    // this.keywords = await axios.get('/keywordRequest');
    //console.log("keywords fetched");
  }, 

  computed: {
    timeSelected() {
      if (this.timeRangeFilter == null || this.timeRangeFilter.length == 0) {
        return false;
      }
      return true;
    }, 
  }, 

  methods: {
    // MAP COMPONENT METHODS
    addTimeParsingFilters(timeResults) {
      if (timeResults.length == 0) {
        // no time was parsed
        return;
      }
      if (timeResults.length != 2) {
        // if timeresults does not have two entries, 
        console.log("error - query analyzer must return exactly 2 timestamps!");
        console.log(timeResults);
        return;
      }
      const startTime = timeResults[0];
      //console.log("start time was parsed as: " + timeResults[0]);
      const endTime = timeResults[1];
      //console.log("end time was parsed as: " + timeResults[1]);
      this.timeRangeFilter = [startTime, endTime];
    }, 
    focusMapOnLocations(locations) {
      // focus map on a list of provided geobounds
      this.initialFocusList = locations;
      if (this.$refs.mapRef == undefined) {
        // map does not exist, cannot focus
        return;
      }
      else {
        this.$refs.mapRef.focusMapOnLocationsList(locations);
      }
    }, 

    // UI STATE METHODS
    refreshUIAfterQuery() {
      // hide map and show top results (should be called after a new query was fetched)
      this.showMap = false;
      this.showTopPublicationResults = true;
      this.showTopSTACResults = true;
    }, 
    showMapClicked() {
      this.showMap = !this.showMap;
    }, 
    clearTimeSelection() {
      this.timeRangeFilter = [];
    }, 
    advancedSearchClick() {
      this.showAdvancedSearch = !this.showAdvancedSearch;
      //this.$refs.op.toggle(event);
    }, 
    closeDocumentList(docListType) {
      // this function is called when a DocumentList emits a 'closing' call
      if (docListType == 'Publications') {
        this.showTopPublicationResults = false;
        return;
      }
      if (docListType == 'STAC Collections') {
        this.showTopSTACResults = false;
        return;
      }
      console.log("warning - closeDocumentList was emitted but docListType is not recognized: " + docListType);
    }, 
    minimizeMap() {
      this.showMap = false;
    }, 
  
    // BACKEND QUERY HELPER METHODS
    getLocationFilter() {
      // return a list of current location filters
      if (this.$refs.mapRef == undefined) {
        // cannot get location filter list if map does not exist
        return null;
      }
      return this.$refs.mapRef.getLocationFilter();
    }, 
    getTimeFilterList() {
      // return a list of current time filters
      if (this.timeRangeFilter.length == null) {
        return [];
      }
      // copy array
      return [this.timeRangeFilter[0], this.timeRangeFilter[1]];
    }, 

    // BACKEND QUERY METHODS
    async submitQuery(userQuery) {
      //console.log("starting to submit query");
      if (userQuery == null) {
        //console.log("no user query provided");
        this.$toast.add({
          severity: 'error', 
          summary: 'No query', 
          detail: 'Please enter a term to search', 
          life: 5000, 
          group: 'tc'
        });
        return;
      }
      this.queryIsLoading = true;

      // first, analyze query and parse location, time and keywords from query
      const analyzerQueryResult = await this.analyzeQueryRequest(userQuery);
      let keywords = null;
      if (analyzerQueryResult.status != 200) {
        console.log("error - query analyzer request failed! " + analyzerQueryResult.status + analyzerQueryResult.statusText);
      }
      else {
        // TODO let users confirm locations and dates
        let geoBoundsList = []
        for (const locationTuple of analyzerQueryResult.data.locations) {
          // const locationName = locationTuple[0];
          const geoBounds = locationTuple[1];
          geoBoundsList.push(geoBounds);
        }
        this.focusMapOnLocations(geoBoundsList);
        this.addTimeParsingFilters(analyzerQueryResult.data.dates);
        keywords = analyzerQueryResult.data.general_keywords;
      }

      // after setting analyzer results from Query Analyzer, continue with normal document query
      await this.makeDocumentQueryRequest(userQuery, keywords);
      this.lastUserQuery = userQuery;
      // let "topResults" appear and hide map
      this.refreshUIAfterQuery();
    }, 
    async makeDocumentQueryRequest(userQuery, keywords) {
      // TODO build in error handling
      const promises = []; 
      if (this.selectPublications) {
        const pubRequest = this.requestPublications(userQuery, keywords);
        promises.push(pubRequest);
      }
      if (this.selectSTACCollections) {
        const stacCollectionRequest = this.requestSTACCollections(userQuery, keywords);
        promises.push(stacCollectionRequest);
      }
      if (this.selectWebDocuments) {
        const webResultRequest = this.requestWebResources(userQuery);
        promises.push(webResultRequest);
      }
      // wait for all queries
      try {
        const responseList = await Promise.all(promises);
        // parse response into documents variable
        for (const singleResponse of responseList) {
          if (singleResponse.status != 200) {
            // request failed
            // TODO print which request failed
            console.log("database request failed!");
            console.log(singleResponse);
            continue;
          }
          const key = singleResponse.data[0];
          console.log("database request for " + key + " was successful!");
          if (key in this.documents) {
            this.documents[key] = singleResponse.data[1];
          }
        }
      } catch(err) {
        alert(err);
      } finally {
        this.queryIsLoading = false;
        if (this.showStartScreen) {
          this.showStartScreen = false;
        }
        // this.showMapAndList();        
      }
    }, 
    validateParamsForStacItemQuery(stacCollectionId, locationFilter, timeFilter) {
      if (locationFilter == null) {
        // abort query if no area is selected
        console.log("no filter area selected -> no STAC query possible");
        this.$toast.add({
          severity: 'warn', 
          summary: 'Select location', 
          detail: 'Please specify location for STAC request!', 
          life: 4000, 
          group: 'tc'
        });
        this.showAdvancedSearch = true;
        return false;
      }
      if (timeFilter.length == 0) {
        // timeRange is not complete: ask user whether to continue
        const parent = this; // used to access 'this' in callback function
        this.$confirm.require({
          message: "No time range selected - Do you want to proceed?", 
          header: "Confirmation", 
          icon: "pi pi-exclamation-triangle", 
          accept: function() {
            // clear time range 
            parent.timeRangeFilter = [];
            parent.continueStackItemQuery(stacCollectionId, locationFilter, timeFilter);
          }, 
          reject: function() {
            parent.$toast.add({
              severity: 'warn', 
              summary: 'Select time range', 
              detail: 'Please specify time range for STAC item query', 
              life: 4000, 
              group: 'tc'
            });
            parent.showAdvancedSearch = true;
          }, 
        });
        return false;
      }
      // continue with stac item query
      return true;
    }, 
    async continueStackItemQuery(stacCollectionId, locationFilter, timeFilter) {
      // set loading True and selected False for all other entries
      if (!(stacCollectionId in this.stacItems)) {
        this.stacItems[stacCollectionId] = {}; 
      }
      let stacRequest = {
        'time_filter': timeFilter, 
        'location_filter': locationFilter, 
        'stac_items': [],
        'selected': false,
        'loading': true, 
      };
      const stacRequestUID = get_uid();
      this.stacItems[stacCollectionId][stacRequestUID] = stacRequest;
      let response = [];
      try {
        response = await this.requestSTACItems(stacCollectionId, locationFilter, timeFilter);
        response = response.data[1];
      }
      catch (err) {
        console.log(err);
        alert("Something went wrong");
        response = [];
      }
      finally {
        // set 'selected' false for all previous entries
        for (const entryUID in this.stacItems[stacCollectionId]) {
          this.stacItems[stacCollectionId][entryUID].selected = false;
        }
        // set properties for new entry
        this.stacItems[stacCollectionId][stacRequestUID].stac_items = response;
        this.stacItems[stacCollectionId][stacRequestUID].loading = false;
        this.stacItems[stacCollectionId][stacRequestUID].selected = true;
      }
    }, 
    async submitStacItemQuery(stacCollectionId) {
      // get location and time filters
      const locationFilter = this.getLocationFilter();
      const timeFilter = this.getTimeFilterList();
      const queryIsValid = this.validateParamsForStacItemQuery(stacCollectionId, locationFilter, timeFilter)
      if (!queryIsValid) {
        // invalid query parameters
        console.log("invalid parameters for STAC query");
        return;
      }
      // continue with Stac item query 
      this.continueStackItemQuery(stacCollectionId, locationFilter, timeFilter);
    }, 
    async downloadSTACNotebook(stacCollectionId) {
      let locationFilter = this.getLocationFilter();
      let timeFilter = this.getTimeFilterList();
      let response = [];
      try {
        response = await this.requestSTACNotebook(stacCollectionId, locationFilter, timeFilter);
        // create blob file and trigger automatic download
        const blob = new Blob([response.data]);
        const link = document.createElement('a');
        link.href = window.URL.createObjectURL(blob);
        link.download = "STAC_Download_Notebook.ipynb";
        link.click();
        URL.revokeObjectURL(link.href);
      }
      catch (err) {
        console.log(err);
        alert("Something went wrong");
        response = [];
      }
      finally {
        console.log("STAC Notebook request finished!");
      }
    }, 
    async requestPublications(userQuery, keywords) {
      const path = '/pubRequest'
      const request = {
        'query': userQuery, 
        'keywords': keywords, 
        'limit': 10, 
      };
      return axios.post(path, request);
    }, 
    async requestWebResources(userQuery) {
      const path = '/webRequest';
      const request = {
        'query': userQuery, 
        'limit': 10, 
      };
      return axios.post(path, request);
    }, 
    async requestSTACCollections(userQuery, keywords) {
      const path = '/stacCollectionRequest';
      const request = {
        'query': userQuery, 
        'keywords': keywords, 
        'limit': 10, 
      };
      return axios.post(path, request);
    }, 
    async requestSTACItems(stacCollectionId, locationFilter, timeInterval) {
      const path = '/stacItemRequest';
      const request = {
        'collection_id': stacCollectionId, 
        'limit': 5, 
        'location_filter': locationFilter, 
        'time_interval': timeInterval
      };
      return axios.post(path, request);
    }, 
    async requestSTACNotebook(stacCollectionId, locationFilter, timeInterval) {
      const path = '/notebookExportRequest';
      const request = {
        'collection_id': stacCollectionId, 
        'location_filter': locationFilter, 
        'time_interval': timeInterval
      }; 
      return axios.post(path, request, {
        responseType: 'arraybuffer'
      });
    }, 
    async analyzeQueryRequest(userQuery) {
      const path = '/queryAnalyzerRequest';
      const request = {
        'query': userQuery
      };
      return axios.post(path, request);
    }, 
    async requestGeotweets() { 
      const path = '/geotweetRequest';
      // TODO: get search parameters from user
      const request = {
        'only_floods': true, 
        'limit': 1000,
      }
      const response = await axios.post(path, request);

      if (response.status != 200) {
        console.log("something went wrong with geotweet request; status code " + response.status);
        return;
      }
      // debug
      // console.log(response.data);
      if (this.$refs.mapRef == null) {
        console.log("warning - cannot display geotweets because map was not created");
        return;
      }
      this.$refs.mapRef.showGeotweets(response.data);
    }, 
  }, 

}
</script>

<style scoped>

#documentBody {
    margin-top: 120px;
}

#appHeader {
    position: fixed;
    width: 100%; 
    z-index: 1;
    top: 0;
}

#searchHeader {
    position: fixed;
    top: 0;
}

#documentListComponent {
    width: 100%;
    margin-left: 1.0rem;
    margin-right: 0.5rem;
}

#mapComponent {
    /* height: 85vh; */
    width: 100%;
    margin-left: auto;
    margin-right:0.5rem;
    padding: 1.0rem;
}

.topResultListComponent {
  width: 90%;
  float: right;
  /* margin-left: auto; */
  margin-right: 0.5rem;
}

.advanced-search-element {
  justify-content: start;
  width: 100%;
  height: auto;

  border-style: solid;
  border-width: 1px;
  border-radius: 5px;

  padding: 0.5rem;
  margin-top: 0.25rem;
  margin-bottom: 0.5rem;
}

.advanced-search-header {
  font-size: 0.75rem;
  font-weight: bold;
}

.advanced-search-body {
  font-size: 0.75rem;
  position: relative;
  display: inline-flex;
}

.center-button {
  margin:0 auto;
  display: block;
}

.column {
  display: inline-block;
  width: 50%;
}


</style>
