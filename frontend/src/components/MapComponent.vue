<template>
  <div>
    <div class="mx-1">
      <PButton
        class="right-button"
        :icon="showMap ? 'pi pi-window-minimize' : 'pi pi-window-maximize'"
        :label="showMap ? 'Hide Map' : 'Show Map'"
        @click="this.$emit('showMapClicked')"
      />
      <PButton v-if="showMap"
        class="right-button mx-1"
        :icon="fixMap ? 'pi pi-lock' : 'pi pi-unlock'"
        :severity="fixMap ? 'danger' : 'success'" 
        v-tooltip="fixMap ? 'Unfix map' : 'Fix map'" 
        @click="this.$emit('fixMapClicked')"
      />
    </div>
    <div 
      class="w-full mx-1 "
      :class="showMap ? 'visible-map' : 'invisible-map'"
    >
      <div class="w-full my-2">
        <SplitButton 
          class="inline-flex mx-2 left-button" 
          severity="success" 
          :icon="polygonSelected ? 'pi pi-caret-up' : 'pi pi-stop'" 
          :model="drawItems"
          size="small"
          label="SELECT AREA" 
          @click="startDrawing" 
        />
        <PButton 
          v-if="isDrawing" 
          class="inline-flex mx-2 left-button" 
          severity="warning" 
          size="small" 
          label="STOP DRAWING"
          @click="stopDrawing"
        />
        <PButton 
          v-if="filterBounds" 
          class="inline-flex mx-2 left-button" 
          severity="warning" 
          size="small" 
          label="CLEAR FILTER"
          @click="clearFilterLayer"
        />
        <PButton 
          class="mx-5 w-2 right-button" 
          severity="danger" 
          size="small" 
          icon="pi pi-trash" 
          label="CLEAR MAP" 
          @click="clearAllLayers"
        />
      </div>
      <div id="mapContainer">
      </div>
    </div>
  </div>
</template>


<script>

import "leaflet/dist/leaflet.css";
import L from "leaflet";
import 'leaflet-draw/dist/leaflet.draw.css';

import { useScriptTag } from '@vueuse/core';

useScriptTag('leaflet-heat.js');

require('leaflet-draw');

export default {

  name: "MapComponent",
  props: {
    documents: Object, // object that holds all documents that should eventually be displayed in the Map component
    stacItems: Object, // object that holds all stac items that have been queried + meta data if it should be displayed etc...
    initialFocusList: Object, // initial focus coordinates when starting the map
    showMap: Boolean, // controls whether the div element is hidden or not
    fixMap: Boolean, // controls whether the map is fixed or not
  },
  inject: ['Utils'],
  emits: [
    'stacItemClicked', // triggers highlighting of stac item in document list
    'showMapClicked', 
    'fixMapClicked', 
  //  'requestGeotweets',   // triggers request to backend to retrieve geotweets (example)
  ], 
  components: {},

  data() {
    return {
      // UI state
      
      // map component
      map: null,
      // map layers
      stacCollectionLayers: {},
      drawnLayers: null, 
      heatLayer: null, 
      spatialExtent: null, 
      // draw controller
      drawControl: null,
      polygonDrawer: null,
      rectangleDrawer: null,
      // filter bounds
      filterBounds: null,
      // UI state elements
      isDrawing: false, 
      polygonSelected: true, 
      drawItems: [
        {
          label: 'Polygon',
          icon: 'pi pi-caret-up',
          command: () => {
            this.polygonSelected = true;
          }
        },
        {
          label: 'Rectangle',
          icon: 'pi pi-stop',
          command: () => {
            this.polygonSelected = false;
          }
        }
      ] 
    }
  },

  methods: {
    // LEAFLET DRAW FUNCTIONS
    startPolygon() {
      // start drawing a polygon
      this.isDrawing = true;
      this.polygonDrawer.enable();
    },
    startRectangle() {
      // end drawing a polygon
      this.isDrawing = true;
      this.rectangleDrawer.enable();
    },
    startDrawing() {
      // start drawing
      this.isDrawing = true;
      if (this.polygonSelected) {
        this.polygonDrawer.enable();
      }
      else {
        this.rectangleDrawer.enable();
      }
    }, 
    stopDrawing() {
      // stop drawing
      this.polygonDrawer.disable();
      this.rectangleDrawer.disable();
      this.isDrawing = false;
    }, 
    // HANDLING LAYERS
    clearAllLayers() {
      // remove filter areas
      this.clearFilterLayer();

      // remove STAC layers
      this.clearSTACLayers();
      this.stacCollectionLayers = {};

      // remove heatmap layer
      if (this.heatLayer !== null) {
        this.map.removeLayer(this.heatLayer);
      }
      this.heatLayer = null;
      // remove spatial extent layer
      this.clearSpatialExtent();
    }, 
    clearSpatialExtent() {
      if (this.spatialExtent !== null) {
        for (const layer of this.spatialExtent.getLayers()) {
          this.map.removeLayer(layer);
        }
      }
      this.spatialExtent = null;
    }, 
    clearSTACLayers() {
      for (const stacCollectionID in this.stacCollectionLayers) {
        for (const requestUID in this.stacCollectionLayers[stacCollectionID]) {
          const layer = this.stacCollectionLayers[stacCollectionID][requestUID];
          this.map.removeLayer(layer);
        }
      }
    }, 
    clearFilterLayer() {
      this.drawnLayers.clearLayers();
      this.filterBounds = null;
    }, 
    getBoundsFromBBox(bbox) {
      // takes bbox [long/lat; long/lat]
      return new L.LatLngBounds([bbox[1], bbox[0]], [bbox[3], bbox[2]]);
    }, 
    getLocationFilter() {
      return this.filterBounds;
    }, 
    // MAP UI FUNCTIONS
    focusGlobal() {
      // min long, min lat, max long, max lat
      const globalBounds = this.getBoundsFromBBox([-180,-90,180,90])
      this.map.fitBounds(globalBounds, {'animate': true});
    }, 
    showSpatialExtent(bboxList) {
      // clear old spatial extent layer
      this.clearSpatialExtent();

      if (bboxList.length == 0) {
        // focus globally if no other bbox is specified
        this.focusGlobal();
        return;
      }
      // create new spatial extent layer
      const spatialExtentFeatureGroup = new L.FeatureGroup();
      let foundBBox = false;
      for (const bbox of bboxList) {
        // check if bbox covers the whole map
        foundBBox = true;
        const bounds = this.getBoundsFromBBox(bbox);
        const layer = new L.Rectangle(bounds, {
          color: 'red', 
          weight: 1
        });
        spatialExtentFeatureGroup.addLayer(layer);
      }
      if (foundBBox) {
        // focus on feature group
        this.map.fitBounds(spatialExtentFeatureGroup.getBounds(), {'animate': true});
        // add to map
        spatialExtentFeatureGroup.addTo(this.map);
      }
      this.spatialExtent = spatialExtentFeatureGroup;

    }, 
    focusMapOnSTACLayer(stacCollectionID, requestUID) {
      if (stacCollectionID in this.stacCollectionLayers && requestUID in this.stacCollectionLayers[stacCollectionID]) {
        const featureGroup = this.stacCollectionLayers[stacCollectionID][requestUID];
        this.map.fitBounds(featureGroup.getBounds(), {'animate': true});
      }
      else {
        console.log("cannot find feature group for stacCollectionID " + stacCollectionID + " and requestUID " + requestUID);
      }
    }, 
    focusMapOnLocationsList(geoBoundsList) {
      // TODO refactor this function (is only used when focusing on geoparsed location from query)
      if (this.map == null) {
        // map was not rendered yet
        console.log("warning - map was not rendered yet; cannot focusMapOnLocationsList");
        return;
      }
      // focus map by using the center of the geobounds list
      if (geoBoundsList == null || geoBoundsList.length == 0) {
        // console.log("the geoBoundsList provided is null, cananot focus list");
        return;
      }
      let initialBounds = null;
      for (const geoBounds of geoBoundsList) {
        // convert 
        let currentBounds = null;
        if (geoBounds.type == 'bbox') {
          currentBounds = this.getBoundsFromBBox(geoBounds.coords);
        }
        else {
          console.log("warning - type " + geoBounds.type + " not implemented in function (focusMap)");
          continue;
        }
        if (initialBounds == null) {
          initialBounds = currentBounds;
        }
        else {
          initialBounds = initialBounds.extend(currentBounds);
        }
      }
      if (initialBounds == null) {
        console.log("warning - could not compute geoBounds for geoBoundsList; focusMap failed");
        console.log(geoBoundsList);
        return;
      }
      this.map.fitBounds(initialBounds, {'animate': true});
    }, 
    requestGeotweets() {
      // example function to show geotweets (used for testing!)
      this.$emit('requestGeotweets');
    }, 
    showGeotweets(geotweets) {

      // display geotweets
      // var geojsonLayer = L.geoJSON().addTo(this.map);
      let tweetLatLongList = [];
      // get center of point cloud
      let xMean = 0;
      let yMean = 0;
      let count = 0;
      for (const tweet of geotweets) {
        // geojsonLayer.addData(tweet);
        tweetLatLongList.push(tweet.geometry.coordinates);
        // add up point coordinates
        xMean += tweet.geometry.coordinates[0];
        yMean += tweet.geometry.coordinates[1];
        count += 1;
      }
      this.addHeatMap(tweetLatLongList);
      xMean /= count;
      yMean /= count;
      this.map.flyTo([xMean,yMean]);
    }, 

    addHeatMap(coordinateList) {
      // adds the coordinate list as a heatmap on the map
      // TODO refactor this function (reusable data structure, clean implementation, use some weight for intensity etc.)
      const weight = 0.5;
      // add intensity as third parameter in list
      let intensityList = [];
      for (const coordinates of coordinateList) {
        const intensity = [coordinates[0], coordinates[1], weight];
        intensityList.push(intensity);
      }
      this.heatLayer = new L.heatLayer(
        intensityList, 
        {
          maxZoom: 3,
          radius: 12, 
          //gradient: {0.4: 'blue', 0.65: 'lime', 1: 'red'}, 
          minOpacity: 0.3, 
        }
      );
      this.heatLayer.addTo(this.map);
    }, 
    async createMap() {
      // this function is called to create a new map instance and initiate "this.map"
      const defaultFocus = [45, 20];
      const defaultZoom = 5;
      await this.waitForElm('#mapContainer');
      this.map = L.map("mapContainer", { 
        drawControl: false, 
        minZoom: 3, 
        maxZoom: 10,
      }).setView(defaultFocus, defaultZoom);
      L.tileLayer("http://{s}.tile.osm.org/{z}/{x}/{y}.png", {
        attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors',
      }).addTo(this.map);

      // enable drawing shapes on map
      // FeatureGroup is to store editable layers
      this.drawnLayers = new L.FeatureGroup();
      this.map.addLayer(this.drawnLayers);
      this.drawControl = new L.Control.Draw({
        position: 'topright', 
        draw: {
          polygon: false, 
          polyline: false, 
          circle: false, 
          rectangle: false, 
          marker: false, 
          circlemarker: false, 
        }, 
        edit: {
          featureGroup: this.drawnLayers
        }
      });
      this.map.addControl(this.drawControl);

      this.polygonDrawer = new L.Draw.Polygon(this.map);
      this.rectangleDrawer = new L.Draw.Rectangle(this.map);

      // add event listeners
      this.map.on(L.Draw.Event.DRAWSTART, () => {
        if (this.filterBounds !== null) {
          console.log("filter already exists - will be deleted now!");
          this.clearFilterLayer();
        }
      });
      
      this.map.on(L.Draw.Event.CREATED, e => {

        e.layer.setStyle({
          color: 'red', 
        });
        
        // handle different shapes (rectangle, polygon)
        // create new layer (cannot use e.layer because of Vue3.JS bug -> does not create Proxy object which causes reactivity issues)
        if (e.layerType == 'rectangle') {
          // we convert rectangle bounds to bbox and store it into coordinates
          const coords = this.Utils.getBBoxFromBounds(e.layer.getBounds())
          this.filterBounds = {
          'type': 'bbox', 
          'coords': coords, 
          };
        } else if (e.layerType == 'polygon') {
          // polygon coords are simply the LatLng lists of the layer
          const coords = e.layer.getLatLngs()
          this.filterBounds = {
          'type': 'polygon', 
          'coords':  coords, 
          };
        } else {
          console.log("warning - unknown layer type: " + e.layerType + "; cannot create drawn layer :(");
          return
        }
        this.drawnLayers.addLayer(e.layer);
        this.isDrawing = false;
      });
    }, 
    waitForElm(selector) {
      // this function waits for the element specified by the selector to appear in the DOM 
      // needed for creating the map!
      // https://stackoverflow.com/questions/5525071/how-to-wait-until-an-element-exists
      return new Promise(resolve => {
        if (document.querySelector(selector)) {
          return resolve(document.querySelector(selector));
        }
        
        const observer = new MutationObserver(() => {
          // console.log(mutations);
          if (document.querySelector(selector)) {
            observer.disconnect();
            resolve(document.querySelector(selector));
          }
        });

        observer.observe(document.body, {
          childList: true, 
          subtree: true
        });
      });
    }, 

  },

  watch: {
    stacItems: {
      handler() {
        console.log("stac item re-rendering triggered!");
        this.clearSTACLayers();
        for (const stacCollectionID in this.stacItems) {
          // stacCollectionDict consists of all requests for a single stac collection
          const stacCollectionDict = this.stacItems[stacCollectionID];
          for (const requestUID in stacCollectionDict) {
            // entry consists of one single request in that stac collection
            const requestDict = stacCollectionDict[requestUID];
            if (!requestDict.selected) {
              continue;
            }
            // create layer for each entry
            const newFeatureGroup = new L.FeatureGroup();
            let color = 'red';
            for (const stacItemID in requestDict.stacItems) {
              const stacItem = requestDict.stacItems[stacItemID]
              // console.log(stacItemID);
              if (stacItemID == requestDict.highlightID) {
                color = 'blue';
                // console.log("highlighting stac item: " + stacItemID);
              }
              else {
                color = 'red';
                // console.log("not highlighting stac item: " + stacItemID);
              }
              const layer = new L.GeoJSON(stacItem, {
                style: {
                  color: color, 
                }
              });
              // add click event listener
              layer.on('click', (e) => {
                const stacCollectionID = e.propagatedFrom.feature.collection;
                const stacItemID = e.propagatedFrom.feature.id;
                const requestUID = e.propagatedFrom.feature.requestUID;
                this.$emit('stacItemClicked', stacCollectionID, requestUID, stacItemID);
              });
              newFeatureGroup.addLayer(layer);
            }
            // newFeatureGroup.setStyle(
            //   function() {
            //     return {color: color}
            //   }
            // );

            // add layer to stacCollectionLayers
            if (this.stacCollectionLayers[stacCollectionID] == null) {
              this.stacCollectionLayers[stacCollectionID] = {};
            }
            this.stacCollectionLayers[stacCollectionID][requestUID] = newFeatureGroup;

            // add layer to map
            newFeatureGroup.addTo(this.map);  
          }
        } 
      }, 
      deep: true, 
    }, 
  }, 

  mounted() {
    // build map
    this.createMap();
    // set initial focus
    this.focusMapOnLocationsList(this.initialFocusList);
  },

  onBeforeUnmount() {
    if (this.map) {
      this.map.remove();
    }
  },
};

</script>


<style scoped>

#mapContainer {
    height: 90%;
    width: 90%;
    display: block;
    margin-left: auto;
    margin-right: auto;
    margin-top: auto;
    margin-bottom: auto;
    z-index: 0;
}

.invisible-map {
  display: none; 
}

.visible-map {
  height: 85vh;
}

</style>
