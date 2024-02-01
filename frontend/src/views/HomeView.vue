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
    <PDialog
      v-model:visible="showSTACRequestAlert" 
      modal 
      :header="'Request STAC Items for Collection ' + stacCollectionID"
      class=""
      contentClass=""
    >
      <div v-if="locationFilter == null">
        <p>
          No location filter selected - please select a location filter in the Map Component to continue
        </p>
      </div>
      <div v-else>
        <PTag 
          v-tooltip="'Location Filter: ' + JSON.stringify(locationFilter)"
          class="my-2 mx-1"
          severity="success"
          icon="pi pi-check"
          icon-pos="right"
          value="Selected location filter"
        />
        <PTag v-if="timeSelected" 
          class="my-2 mx-1"
          severity="success"
          icon="pi pi-check"
          icon-pos="right"
          value="Selected time filter"
        />
        <div class="advanced-search-element">
          <label for="datepicker" class="font-bold block mb-2">Select Time Range (optional)</label>
          <VueDatePicker 
            id="datepicker"
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
        <div class="advanced-search-element">
          <label for="integeronly" class="font-bold block mb-2">Specify STAC item limit</label>
          <InputNumber 
            v-model="stacLimit" 
            inputId="integeronly" 
            :min="5"
            :max="500"
          />
        </div>
      </div>
      <div>
        <PButton 
          class="dialog-button"
          severity="danger"
          icon="pi pi-times"
          label="Cancel"
          @click="showSTACRequestAlert = false"
        />
        <PButton v-if="locationFilter != null"
          class="dialog-button"
          severity="success"
          icon="pi pi-check"
          label="Submit STAC Request"
          @click="continueStacItemQuery(this.stacCollectionID)"
        />
      </div>
    </PDialog>
    <div v-if="showStartScreen">
      <div 
        id="appHeader" 
        class="text-xl font-bold py-4 bg-primary">
        <header>
          OpenSearch@DLR (Prototype Development)
        </header>
      </div>
      <!-- START SCREEN -->
      <SearchHeaderComponent 
        class="center"
        :queryIsLoading="queryIsLoading" 
        :showAdvancedSearch="showAdvancedSearch" 
        :show-advanced-search-button="false"
        placeholder="Start your search here..." 
        @submitQuery="this.submitQuery" 
        @advancedSearchClick="this.advancedSearchClick"
      />
    </div>
    <div v-else>
      <!-- "NORMAL" SCREEN -->
      <SearchHeaderComponent 
        ref="searchHeaderRef"
        id="searchHeader" 
        class="center-x surface-ground z-1"
        :queryIsLoading="queryIsLoading" 
        :showAdvancedSearch="showAdvancedSearch"
        :show-advanced-search-button="true"
        :homeViewQuery="homeViewQuery"
        :keywords="keywords"
        :authors="authors"
        @submitQuery="this.submitQuery" 
        @advancedSearchClick="this.advancedSearchClick"
        @graph-query="submitGraphQuery"
        @apply-filter="filterDocuments"
      />
      <div :id="showAdvancedSearch ? 'documentBodyExtended' : 'documentBody'" 
        class=" surface-ground flex">
        <div class="left-column">
          <DocumentListComponent
            id="documentListComponent"
            :documents="filteredDocuments" 
            :stacItems="stacItems" 
            initial-document-type="Web Documents"
            :show-top-results-only="false"
            :search-query="lastUserQuery"
            @submitStacItemQuery="submitStacItemQuery" 
            @downloadSTACNotebook="downloadSTACNotebook"
            @stacItemClicked="stacItemClicked"
            @showSTACItemsOnMap="showSTACItemsOnMap"
            @showSpatialExtent="showSpatialExtent"
            @keyword-clicked="keywordClicked"
            @show-geodata="showGeodata"
            @author-clicked="authorClicked"  
          />
        </div>
        <div class="right-column">
          <MapComponent 
            :class="fixMap ? 'mapComponentFixed surface-ground' : 'mapComponentNormal'"
            ref="mapRef"
            :documents="documents" 
            :stacItems="stacItems" 
            :initial-focus-list="initialFocusList"
            :show-map="showMap"
            :fix-map="fixMap"
            @show-map-clicked="showMapClicked"
            @stacItemClicked="stacItemClicked"
            @fixMapClicked="fixMapClicked" 
            @clearSTACLayers="clearSTACLayers"
            @web-document-clicked-in-map="webDocumentClickedInMap"
          />
          <div v-if="showTopSTACResults">
            <DocumentListComponent
              class="topResultListComponent"
              :documents="documents" 
              :stacItems="stacItems" 
              initial-document-type="STAC Collections"
              :is-top-results-list="true"
              :search-query="lastUserQuery"
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
      rawDocuments: {
        'publications': [],  
        'stac_collections': [], 
        'web_documents': [],
      }, 
      filteredDocuments: null, 
      // stacItems contain all the fetched STAC items frmo this user session
      stacItems: {}, 
      keywords: [], 
      authors: [], 

      // last user query (used to be shown in DocumentList elements)
      lastUserQuery: null,
      
      // homeViewQuery is used as a 'prop' in SearchHeaderComponent and can be used to override userQuery attribute 
      homeViewQuery: null,

      // UI STATE VARIABLES
      showStartScreen: true, 
      // user input
      queryIsLoading: false,
      // advanced search
      showAdvancedSearch: false, 
      // control which elements are shown
      showMap: true, 
      fixMap: false, 
      showTopSTACResults: true, 
      showTopPublicationResults: true, 
      // alert for STAC request
      showSTACRequestAlert: false,
      stacCollectionID: null,
      locationFilter: null, 
      stacLimit: 50, 

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
    const keywordResponse = await axios.get('/keywordRequest');
    if (keywordResponse.status != 200) {
      console.log("error - could not fetch keywords from database");
      return;
    }
    this.keywords = keywordResponse.data;
    
    const authorResponse = await axios.get('/authorRequest');
    if (authorResponse.status != 200) {
      console.log("error - could not fetch authors from database");
      return;
    }
    this.authors = authorResponse.data;
  }, 

  computed: {
    timeSelected() {
      if (this.timeRangeFilter == null || this.timeRangeFilter.length == 0) {
        return false;
      }
      return true;
    }, 
    documents() {
      // placeholder function
      return this.filteredDocuments;
    }, 
    timeFilter() {
      // return time filter as list of two timestamps
      if (this.timeRangeFilter.length == 0) {
        return [];
      }
      return [this.timeRangeFilter[0], this.timeRangeFilter[1]];
    }
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
    fixMapClicked() {
      this.fixMap = !this.fixMap;
    }, 
    clearSTACLayers() {
      // unselect all STAC items
      for (const stacID in this.stacItems) {
        this.stacItems[stacID].selected = false;
      }
    }, 
    // STAC item handler methods
    stacItemClicked(stacCollectionID, requestUID, stacItemID) {
      // STAC item was clicked in map component -> set highlightID to indicate which one was clicked
      this.stacItems[stacCollectionID]['requests'][requestUID].highlightID = stacItemID;
    },
    showSTACItemsOnMap(stacCollectionID, requestUID) {
      // console.log("show stac items on map");
      // console.log(stacCollectionID);
      // console.log(requestUID);
      this.focusOnMap();
      if (this.$refs.mapRef !== undefined) {
        this.$refs.mapRef.focusMapOnSTACLayer(stacCollectionID, requestUID);
      }
    }, 
    showSpatialExtent(bboxList) {
      this.focusOnMap();
      if (this.$refs.mapRef) {
        this.$refs.mapRef.showSpatialExtent(bboxList);
      }
    }, 
    showGeodata(location) {
      // show geodata from web items on map
      this.showWebDocumentsOnMap();
      this.focusOnMap();
      if (this.$refs.mapRef) {
        this.$refs.mapRef.showGeodata(location);
      }
    }, 
    webDocumentClickedInMap(webDocId) {
      for (const webDoc of this.documents.web_documents) {
        if (webDoc.id == webDocId) {
          window.open(webDoc.url);
          return;
        }
      }
      console.log("error - did not find web document for " + webDocId);
    }, 

    showWebDocumentsOnMap() {
      if (this.$refs.mapRef) {
        this.$refs.mapRef.createWebDocumentLayer();
      }
    }, 

    // UI STATE METHODS
    copyRawDocuments() {
      // deep copy of rawDocuments
      let documents = {
        'publications': [],  
        'stac_collections': [], 
        'web_documents': [],
      };
      for (const pub of this.rawDocuments.publications) {
        documents.publications.push(pub);
      }
      for (const stacColl of this.rawDocuments.stac_collections) {
        documents.stac_collections.push(stacColl);
      }
      for (const webDoc of this.rawDocuments.web_documents) {
        documents.web_documents.push(webDoc);
      }

      return documents;

    },
    
    // graph / filter helper methods
    resetFilters() {
      if (this.$refs.searchHeaderRef) {
        this.$refs.searchHeaderRef.selectedKeywords = [];
        this.$refs.searchHeaderRef.selectedAuthors = []; 
      }
      else {
        console.log("warning - cannot reset filters because search header ref does not exist");
      }
    }, 

    filterDocuments(selectedKeywords, selectedAuthors) {
      // whenever this method is run, the documents get updated based on the current filters that are applied
      if (!this.$refs.searchHeaderRef) {
        this.filteredDocuments = this.copyRawDocuments();
        return;
      }
      // check which filtering should be applied
      let filterKeywordsFlag = false;
      let filterAuthorsFlag = false;
      let filterPublicationsFlag = false;
      let filterSTACCollectionsFlag = false;

      // only apply filters if there is at least one keyword / author present in the selected array
      if (selectedKeywords.length > 0) {
        // keywords for filtering are present
        filterKeywordsFlag = true;
        filterPublicationsFlag = true;
        filterSTACCollectionsFlag = true;
        
        selectedKeywords = selectedKeywords.map(function(keyword) {
          return keyword.id;
        });

      }
      if (selectedAuthors.length > 0) {
        // authors for filtering are present
        filterAuthorsFlag = true;
        filterPublicationsFlag = true;
        selectedAuthors = selectedAuthors.map(function(author) {
          return author.id;
        });
      }

      if (!filterKeywordsFlag && !filterAuthorsFlag) {
        this.filteredDocuments = this.copyRawDocuments();
        return;
      }

      // do the filtering on the document lists
      let documents = this.copyRawDocuments();
      let includeDocument = true;
      if (filterPublicationsFlag) {
        let filteredPublications = []; 
        
        for (const pub of documents.publications) {
          includeDocument = true;
          if (filterKeywordsFlag) {
            includeDocument = false;
            for (const keywordNode of pub.keywords) {
              if (selectedKeywords.includes(keywordNode.keyword._id)) {
                includeDocument = true;
                break;
              }
            }
          }
          if (!includeDocument) {
            // publication does not qualify -> continue
            continue;
          }

          if (filterAuthorsFlag) {
            includeDocument = false;
            for (const authorNode of pub.authors) {
              if (selectedAuthors.includes(authorNode.author._id)) {
                includeDocument = true;
                break;
              }
            }
          }
          if (includeDocument) {
            filteredPublications.push(pub);
          }
        }
        documents.publications = filteredPublications;
      }

      if (filterSTACCollectionsFlag) {
        let filteredSTACCollections = []; 
        for (const stacColl of documents.stac_collections) {
          includeDocument = false;
          for (const keywordNode of stacColl.keywords) {
            if (selectedKeywords.includes(keywordNode.keyword._id)) {
              includeDocument = true;
              break;
            }
          }
          if (includeDocument) {
            filteredSTACCollections.push(stacColl);
          }
        }
        documents.stac_collections = filteredSTACCollections
      }
      this.filteredDocuments = documents;

    }, 
    refreshUIAfterQuery() {
      // hide map and show top results (should be called after a new query was fetched)
      this.showMap = false;
      this.showTopPublicationResults = true;
      this.showTopSTACResults = true;
    }, 
    focusOnMap() {
      // sets showMap to true and scrolls to map element
      this.showMap = true;
      if (this.$refs.mapRef == null) {
        return;
      }
      this.$refs.mapRef.$el.scrollIntoView({behavior:'smooth'});
    }, 
    showMapClicked() {
      this.showMap = !this.showMap;
      if (!this.showMap) {
        this.fixMap = false;
      }
      if (this.showMap) {
        this.$refs.mapRef.createWebDocumentLayer();
      }
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
    // DOCUMENT LIST COMPONENT METHODS
    keywordClicked(keyword) {
      // user clicked on a keyword in a document -> submit query with keyword
      // this.homeViewQuery = keyword;
      // this.submitQuery(keyword);
      // user clicked on a keyword in a document -> add to selected Keywords from search component (and activate advanced search)
      if (this.$refs.searchHeaderRef && !this.$refs.searchHeaderRef.selectedKeywords.includes(keyword)) {
        this.$refs.searchHeaderRef.selectedKeywords.push(keyword);
      }
      this.showAdvancedSearch = true;
    },
    authorClicked(author) {
      if (this.$refs.searchHeaderRef && !this.$refs.searchHeaderRef.selectedAuthors.includes(author)) {
        this.$refs.searchHeaderRef.selectedAuthors.push(author);
      }
      this.showAdvancedSearch = true;
    }, 

    async submitGraphQuery(keywords, authors) {
      // graph key
      const request = {
        'keywords': keywords, 
        'authors': authors, 
      }
      const response = await axios.post('/graphQueryRequest', request);
      if (response.status  != 200) {
        console.log("error - could not fetch graph query");
        return;
      }
      // parse response
      this.rawDocuments['stac_collections'] = response.data.stac_collections;
      this.rawDocuments['publications'] = response.data.publications;

      // TODO set last user query to graph search
      this.lastUserQuery = "Graph Search";

      // reset filters after graph query
      this.resetFilters();
      this.filterDocuments([], []);

      // TODO what happens with web data ?
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
    // BACKEND QUERY METHODS
    async submitQuery(userQuery) {
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
      this.locationFilter = this.getLocationFilter();
      await this.makeDocumentQueryRequest(userQuery, keywords);
      this.lastUserQuery = userQuery;
      this.homeViewQuery = userQuery;
      // let "topResults" appear and hide map
      this.refreshUIAfterQuery();
    }, 

    async makeDocumentQueryRequest(userQuery, keywords) {
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
            console.log("database request failed!");
            console.log(singleResponse);
            continue;
          }
          const key = singleResponse.data[0];
          console.log("database request for " + key + " was successful!");
          if (key in this.rawDocuments) {
            this.rawDocuments[key] = singleResponse.data[1];
          }
        }
      } catch(err) {
        alert(err);
      } finally {
        this.queryIsLoading = false;
        if (this.showStartScreen) {
          this.showStartScreen = false;
        }
        // make web documents visible in map
        this.showWebDocumentsOnMap();
        
        // reset filters
        this.resetFilters();
        this.filterDocuments([], []);
      }
    }, 
    async continueStacItemQuery(stacCollectionID) {
      this.showSTACRequestAlert = false;
      // set loading True and selected False for all other entries
      if (!(stacCollectionID in this.stacItems)) {
        this.stacItems[stacCollectionID] = {
          'selected': false, 
          'requests' : {}
        }; 
      }
      let stacRequest = {
        'timeFilter': this.timeFilter, 
        'locationFilter': this.locationFilter, 
        'stacItems': [], 
        'selected': false, 
        'loading': true, 
        'highlightID': null, // if some STAC item is clicked, highlightID indicates which one
      };
      const stacRequestUID = get_uid();
      this.stacItems[stacCollectionID]['requests'][stacRequestUID] = stacRequest;
      let stacItemsDict = {};
      try {
        const response = await this.requestSTACItems(stacCollectionID, this.locationFilter, this.timeFilter);
        // transform list of STAC items (dictionaries) into dictionary of STAC items (key: uid)
        for (const stacDict of response.data[1]) {
          stacItemsDict[stacDict.id] = stacDict;
          // add stacRequestUID to identify stacItem later
          stacItemsDict[stacDict.id].requestUID = stacRequestUID;
        }
      }
      catch (err) {
        console.log(err);
        alert("Something went wrong");
        stacItemsDict = {};
      }
      finally {
        if (Object.keys(stacItemsDict).length == 0) {
          // no STAC items were returned -> alert user and delete request
          this.$toast.add({
            severity: 'error', 
            summary: 'STAC item query failed', 
            detail: 'Unfortunately, there were no results for your STAC query!', 
            life: 4000, 
            group: 'tc'
          });
          delete this.stacItems[stacCollectionID]['requests'][stacRequestUID];
        }
        else {
          // set 'selected' false for all previous entries (both on STAC collection and request level)
          // stac collection level
          for (const stacID in this.stacItems) {
            this.stacItems[stacID].selected = false;
          }
          // request level
          for (const entryUID in this.stacItems[stacCollectionID]['requests']) {
            this.stacItems[stacCollectionID]['requests'][entryUID].selected = false;
          }
          // set properties for new entry
          this.stacItems[stacCollectionID].selected = true;
          this.stacItems[stacCollectionID]['requests'][stacRequestUID].stacItems = stacItemsDict;
          this.stacItems[stacCollectionID]['requests'][stacRequestUID].loading = false;
          this.stacItems[stacCollectionID]['requests'][stacRequestUID].selected = true;
        }

      }
    }, 
    async submitStacItemQuery(stacCollectionID) {
      // open alert
      this.stacCollectionID = stacCollectionID;
      this.locationFilter = this.getLocationFilter();
      this.showSTACRequestAlert = true;
    }, 
    async downloadSTACNotebook(stacCollectionID) {
      let locationFilter = this.getLocationFilter();
      // let timeFilter = this.getTimeFilterList();
      let response = [];
      try {
        response = await this.requestSTACNotebook(stacCollectionID, locationFilter, this.timeFilter);
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
        'location_filter': this.locationFilter
      };
      console.log(request);
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
    async requestSTACItems(stacCollectionID, locationFilter, timeInterval) {
      const path = '/stacItemRequest';
      const request = {
        'collection_id': stacCollectionID, 
        'limit': this.stacLimit, 
        'location_filter': locationFilter, 
        'time_interval': timeInterval
      };
      return axios.post(path, request);
    }, 
    async requestSTACNotebook(stacCollectionID, locationFilter, timeInterval) {
      const path = '/notebookExportRequest';
      const request = {
        'collection_id': stacCollectionID, 
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
      this.focusOnMap();
      this.$refs.mapRef.showGeotweets(response.data);
    }, 
  }, 

}
</script>

<style scoped>

#documentBody {
    margin-top: 120px;
}

#documentBodyExtended {
    margin-top: 245px;
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
    width: 100%;
    margin-left: auto;
    margin-right:0.5rem;
    padding: 1.0rem;
}

.stacDialog {
  width: 50% !important;
  height: 50% !important;
  background-color: aliceblue;
}

.mapComponentNormal {
    width: 100%;
    margin-left: auto;
    margin-right:0.5rem;
    padding: 1.0rem;
    z-index: 1;
}

.mapComponentFixed {
    position: fixed;
    width: 91vh;
    height:100vh;
    padding-top: 1.0rem;
    z-index: 1;
    right:0
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

.dialog-button {
  float: left;
  margin: 0.2rem;
}

.left-column {
  display: inline-block;
  width: 55%;
}

.right-column {
  display: inline-block;
  width: 45%;
}


</style>
