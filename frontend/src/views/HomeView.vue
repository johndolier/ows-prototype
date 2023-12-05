<template>
  <div class="home h-screen w-screen">
        <div class="w-full text-xl font-bold text-primary py-2 my-1 bg-primary">
      <header>OpenSearch@DLR Prototype</header>
    </div>
    <PToast position="top-center" group="tc" />
    <PToast position="top-left" group="tl" />
    <ConfirmDialog></ConfirmDialog>
    <!-- Siebar component for advanced query and filtering documents -->
    <PSidebar v-model:visible="showAdvancedSearch" position="left" :modal="false">
      <h2>
        Advanced Search
      </h2>
      <div class="advanced-search-element">
        <p align="left" class="advanced-search-header">Data types</p>
        <MultiSelect 
          v-model="selectedDatatypes" :options="dataTypes" optionLabel="name" placeholder="Select data types"
          :maxSelectedLabels="3" class="advanced-search-body" panel-class="text-xs">
        </MultiSelect>
      </div>
      <div class="advanced-search-element">
        <p align="left" class="advanced-search-header">Location Filter</p>
        <LocationFilterComponentVue 
          @selectMapCoordinates="selectMapCoordinates"
          class="advanced-search-body"
        />
      </div>
      <div class="advanced-search-element">
        <p align="left" class="advanced-search-header">Time Filter</p>
        <VueDatePicker v-model="timeRangeFilter" range :partial-range="false" class="advanced-search-body"/>
      </div>
    </PSidebar>

    <div v-if="showStartScreen">
      <!-- START SCREEN -->
      <SearchHeaderComponent class="center"
      :queryIsLoading="queryIsLoading" :showAdvancedSearch="showAdvancedSearch" startText="Start your search here..." 
      @submitQuery="this.submitQuery" @advancedSearchClick="this.advancedSearchClick"
      />
    </div>
    <div v-else>
      <!-- "NORMAL" SCREEN -->
      <SearchHeaderComponent class="center-x"
        :queryIsLoading="queryIsLoading" :showAdvancedSearch="showAdvancedSearch"
        @submitQuery="this.submitQuery" @advancedSearchClick="this.advancedSearchClick"
      />
      <div v-if="showDocumentBody" class="w-full z-1">
        <div class="w-full py-2 my-1">
          <SelectButton 
            v-model="viewSelected" :options="viewOptions" optionValue="value" multiple aria-labelledby="multiple">
            <template #option="slotProps">
              <i :class="slotProps.option.icon"></i>
            </template>
          </SelectButton>
        </div>
        <div class="w-screen h-screen flex">
          <!--TODO find better way to dynamically show map and document list-->
          <DocumentListComponent v-if="[1,3].includes(viewMode)"
            :documents="documents" :includeSTACCollections="selectSTACCollections" :includeSTACItems="selectSTACItems" 
            :includePubs="selectPublications" :includeWebDocuments="selectWebDocuments" :stacItems="permanentData.stac_collections" 
            @submitStacItemQuery="submitStacItemQuery" @downloadSTACNotebook="downloadSTACNotebook"
            class="document-list-component">
          </DocumentListComponent>
          <MapComponent v-if="[2,3].includes(viewMode)"
            class="map-component" ref="mapRef"
            :documents="documents" :stacItems="permanentData.stac_collections" :initial-location-filters="locationFilterList"
            @add-location-filter="addLocationFilter" @clear-all-location-filters="clearAllLocationFilters" @requestGeotweets="requestGeotweets" 
            @update-location-filter-list="updateLocationFilterList" @focus-map-on-location-filters="focusMapOnLocationFilters"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
// @ is an alias to /src
import MapComponent from '@/components/MapComponent.vue';
import DocumentListComponent from '@/components/DocumentListComponent.vue';
import LocationFilterComponentVue from '@/components/LocationFilterComponent.vue';
import SearchHeaderComponent from '@/components/SearchHeaderComponent.vue';

import axios from 'axios';

import { v4 as get_uid } from 'uuid';


export default {
  name: 'HomeView',
  components: {
    MapComponent,
    DocumentListComponent, 
    LocationFilterComponentVue, 
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
      // holds "permanent state" for each user session 
      // for now, it consists of stac collections + items mainly
      permanentData: {
        'stac_collections': {}, 
      }, 

      // view control variables
      viewOptions: [
        { icon: 'pi pi-bars', value: "List" },
        { icon: 'pi pi-map', value: "Map" },
      ],
      viewSelected: ["Map"], 
      showDocumentBody: true, 
      showStartScreen: true, 
      // user input
      queryIsLoading: false,
      keywords: null, 
      // FILTERS
      timeRangeFilter: [], 
      locationFilterList: [], 
      // advanced search
      showAdvancedSearch: false, 
      // data types to select 
      selectedDatatypes: [], 
      dataTypes: [
        {'name': 'Publications', 'code': 'pubs'}, 
        {'name': 'STAC Collections', 'code': 'stac_collections'}, 
        {'name': 'Web Data', 'code': 'web'}, 
        {'name': 'STAC Items', 'code': 'stac_items'},      
      ], 
    }
  }, 

  async created() {
    this.keywords = await axios.get('/keywordRequest');
    //console.log("keywords fetched");
  }, 

  mounted() {
    this.selectedDatatypes = [
      //{'name': 'STAC Collections', 'code': 'stac_collections'}, 
      //{'name': 'Publications', 'code': 'pubs'}, 
    ]; 
    //this.submitQuery().then(console.log("query loaded"));
  }, 

  computed: {
    viewMode() {
      if (this.viewSelected.includes("List") && this.viewSelected.includes("Map")) {
        // split mode
        return 3;
      }
      if (this.viewSelected.includes("List")) {
        // list mode
        return 1;
      }
      if (this.viewSelected.includes("Map")) {
        // map mode
        return 2;
      }
      // undefined
      return 4; 
    }, 
    selectPublications() {
      if (this.selectedDatatypes == null || !this.selectedDatatypes.length) {
        return true;
      }
      for (const selectedValue of this.selectedDatatypes) {
        if (selectedValue.code == 'pubs') {
          return true;
        }
      }
      return false;
    }, 
    selectSTACCollections() {
      if (this.selectedDatatypes == null || !this.selectedDatatypes.length) {
        return true;
      }
      for (const selectedValue of this.selectedDatatypes) {
        if (selectedValue.code == 'stac_collections') {
          return true;
        }
      }
      return false;
    }, 
    selectSTACItems() {
      if (this.selectedDatatypes == null || !this.selectedDatatypes.length) {
        return true;
      }
      for (const selectedValue of this.selectedDatatypes) {
        if (selectedValue.code == 'stac_items') {
          return true;
        }
      }
      return false;
    }, 
    selectWebDocuments() {
      if (this.selectedDatatypes == null || !this.selectedDatatypes.length) {
        return true;
      }
      for (const selectedValue of this.selectedDatatypes) {
        if (selectedValue.code == 'web') {
          return true;
        }
      }
      return false;
    }, 
  }, 

  methods: {
    // MAP COMPONENT METHODS
    selectMapCoordinates() {
      // enable filter area drawing in map component
      this.$toast.add({
          severity: 'warn', 
          summary: 'Select area', 
          detail: 'Please select area in map for filtering', 
          life: 5000, 
          group: 'tc'
      });
      // close sidebar
      this.showAdvancedSearch = false;
      // show document body and map to select 
      this.showDocumentBody = true;
      this.showMap();

      // TODO wait until map is mounted! (implement correct function)
      function wait() {
        console.log("waiting...");
      }
      
      while (this.$refs.mapRef === undefined) {
        console.log("set timeout");
        setTimeout(wait, 1000);
      }
      // call selectCoordinates once the map is mounted
      this.$refs.mapRef.selectCoordinates();
    }, 
    updateLocationFilterList(id, layer) {
      // this function can be used by the map component to add a layer into the locationFilterList
      this.locationFilterList[id].layer = layer;
    }, 
    addLocationFilter(id, geoBounds) {
      if (this.locationFilterList.find((element) => element.id == id) !== undefined) {
        // id is already in list
        console.log("warning - cannot add filter with id: " + id + " because it is already present in filter list");
        return;
      }
      // only allow bbox or polygon to be added to location filter list!
      if (!['bbox', 'polygon'].includes(geoBounds.type)) {
        // TODO automatically convert other types?
        console.log("warning - unknown geoBounds type: " + geoBounds.type + "; cannot creaete location filter (addLocationFilter)");
        return;
      }

      let layer = null;
      if (this.$refs.mapRef != undefined) {
        layer = this.$refs.mapRef.addLocationFilterLayer(geoBounds);
      }
      // else -> map was not created yet

      const filterObj = {
        'id': id, 
        'layer': layer, 
        'geoBounds': geoBounds, 
      }; 
      this.locationFilterList.push(filterObj);
    }, 
    removeLocationFilter(id) {
      const filterObj = this.locationFilterList.find((element) => element.id == id);
      if (filterObj == undefined) {
        console.log("warning - did not find id: " + id + " in locationFilterList; cannot remove filter!");
        return;
      }
      this.$refs.mapRef.removeFilterLayer(filterObj.layer)
      // remove filter from list
      this.locationFilterList = this.locationFilterList.filter((element) => element.id != id);
    },
    clearAllLocationFilters() {
      for (const filter of this.locationFilterList) {
        this.removeLocationFilter(filter.id);
      }
      this.locationFilterList = [];
    },
    addGeoparsingLocationFilters(locationResults) {
      // adds location filter results from geoparsing location request
      if (locationResults.length == 0) {
        // no locations returned from geoparsing
        return;
      }
      // TODO ask users for confirmation of locations

      // create location filters in map and add to list
      for (const locationObj of locationResults) {
        // add filter for each found location
        const bounds = locationObj[1];
        const id = get_uid();
        this.addLocationFilter(id, bounds);
      }
      // focus map
      this.focusMapOnLocationFilters();

    }, 
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
    focusMapOnLocationFilters() {
      // focus map on existing location filters if they exist
      if (this.$refs.mapRef == undefined) {
        // map does not exist, cannot focus
        console.log("warning - map does not exist, therefore cannot focus on location filters (likely a startscreen problem)");
        return;
      }
      let geoBoundsList = [];
      for (const filterObj of this.locationFilterList) {
        // add filter for each found location
        const bounds = filterObj.geoBounds;
        if (bounds != undefined) {
          geoBoundsList.push(bounds);
        }
      }
      this.$refs.mapRef.focusMap(geoBoundsList);
    }, 

    // UI STATE METHODS
    advancedSearchClick() {
      this.showAdvancedSearch = !this.showAdvancedSearch;
      //this.$refs.op.toggle(event);
    }, 
    showMap(showOnly) {
      if (showOnly) {
        this.viewSelected = [];
      }
      if (!this.viewSelected.includes("Map")) {
        this.viewSelected.push("Map");
      }
    }, 
    showDocumentList(showOnly) {
      if (showOnly) {
        this.viewSelected = [];
      }
      if (!this.viewSelected.includes("List")) {
        this.viewSelected.push("List");
      }
    }, 
    showMapAndList() {
      this.viewSelected = ["Map", "List"];
    }, 
  
    // BACKEND QUERY HELPER METHODS
    getLocationFilterList() {
      // return a list of current location filters
      let locationFilters = [];
      for (const filter_obj of this.locationFilterList) {
        // extract geographical information for stac item request
        locationFilters.push(filter_obj.geoBounds);
      }
      return locationFilters;
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
        this.addGeoparsingLocationFilters(analyzerQueryResult.data.locations);
        this.addTimeParsingFilters(analyzerQueryResult.data.dates);
        keywords = analyzerQueryResult.data.general_keywords;
      }

      // after setting analyzer results from Query Analyzer, continue with normal document query
      await this.makeDocumentQueryRequest(userQuery, keywords);
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
        this.showDocumentBody = true;
      } catch(err) {
        alert(err);
        this.showDocumentBody = false;
      } finally {
        this.queryIsLoading = false;
        if (this.showStartScreen) {
          this.showStartScreen = false;
        }
        this.showMapAndList();        
      }
    }, 

    validateParamsForStacItemQuery(stacCollectionId) {
      if (this.locationFilterList.length == 0) {
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
      if (this.timeRangeFilter.length == 0) {
        // timeRange is not complete: ask user whether to continue
        const parent = this; // used to access 'this' in callback function
        this.$confirm.require({
          message: "No time range selected - Do you want to proceed?", 
          header: "Confirmation", 
          icon: "pi pi-exclamation-triangle", 
          accept: function() {
            // clear time range 
            parent.timeRangeFilter = [];
            parent.continueStackItemQuery(stacCollectionId);
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

    async continueStackItemQuery(stacCollectionId) {
      // TODO check if entry is already present
      let locationFilters = this.getLocationFilterList();
      let requestTimeFilter = this.getTimeFilterList();

      // set loading True and selected False for all other entries
      if (!(stacCollectionId in this.permanentData.stac_collections)) {
        this.permanentData.stac_collections[stacCollectionId] = []; 
      }
      let stacRequest = {
        'time_filter': requestTimeFilter, 
        'location_filters': locationFilters, 
        'stac_items': [],
        'selected': false,
        'loading': true, 
      };
      this.permanentData.stac_collections[stacCollectionId].push(stacRequest);
      const stacRequestIdx = this.permanentData.stac_collections[stacCollectionId].length - 1; // idx of stac request
      let response = [];
      try {
        response = await this.requestSTACItems(stacCollectionId, locationFilters, requestTimeFilter);
        response = response.data[1];
      }
      catch (err) {
        console.log(err);
        alert("Something went wrong");
        response = [];
      }
      finally {
        // set 'selected' false for all previous entries
        for (const entry of this.permanentData.stac_collections[stacCollectionId]) {
          entry.selected = false;
        }
        // set properties for new entry
        this.permanentData.stac_collections[stacCollectionId][stacRequestIdx].stac_items = response;
        this.permanentData.stac_collections[stacCollectionId][stacRequestIdx].loading = false;
        this.permanentData.stac_collections[stacCollectionId][stacRequestIdx].selected = true;
      }
    }, 

    async submitStacItemQuery(stacCollectionId) {
      if (!this.validateParamsForStacItemQuery(stacCollectionId)) {
        // invalid query parameters
        console.log("invalid parameters for STAC query");
        return;
      }
      // continue with Stac item query 
      this.continueStackItemQuery(stacCollectionId);
    }, 

    async downloadSTACNotebook(stacCollectionId) {
      let locationFilters = this.getLocationFilterList();
      let requestTimeFilter = this.getTimeFilterList();
      let response = [];
      try {
        response = await this.requestSTACNotebook(stacCollectionId, locationFilters, requestTimeFilter);
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
    async requestSTACItems(stacCollectionId, locationFilters, timeInterval) {
      const path = '/stacItemRequest';
      const request = {
        'collection_id': stacCollectionId, 
        'limit': 50, 
        'location_filters': locationFilters, 
        'time_interval': timeInterval
      };
      return axios.post(path, request);
    }, 
    async requestSTACNotebook(stacCollectionId, locationFilters, timeInterval) {
      const path = '/notebookExportRequest';
      const request = {
        'collection_id': stacCollectionId, 
        'location_filters': locationFilters, 
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
      console.log(response.data);

      this.$refs.mapRef.showGeotweets(response.data);
    }, 
  }, 

  watch: {
    viewMode() {
      // this triggers a re-render of the map component in order to avoid issues with invalid leaflet map sizes
      // see https://stackoverflow.com/questions/36246815/data-toggle-tab-does-not-download-leaflet-map/36257493#36257493
      //console.log("triggered invalidate size");
      window.dispatchEvent(new Event('resize'));
      //this.$refs.mapRef.map.invalidateSize();
    }
  }, 

}
</script>


