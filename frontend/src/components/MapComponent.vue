<template>
  <div class="h-full w-full mx-1 ">
    <div class="w-full my-2">
      <PButton 
        class="inline-flex mx-2 left-button" 
        severity="info" 
        size="small" 
        label="SHOW GEOTWEETS (DEBUG)"
        @click="requestGeotweets" 
      />
      <SplitButton 
        class="inline-flex mx-2 left-button" 
        severity="success" 
        :icon="polygonSelected ? 'pi pi-caret-up' : 'pi pi-stop'" 
        :model="drawItems"
        label="SELECT AREA" 
        @click="startDrawing" 
      />
      <PButton 
        v-if="isDrawing" class="inline-flex mx-2 left-button" 
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
    <div id="mapContainer" class="">
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
  },
  inject: ['Utils'],
  emits: [
    'requestGeotweets',   // triggers request to backend to retrieve geotweets (example)
  ], 
  components: {},

  data() {
    return {
      map: null,
      // map layers
      stacCollectionLayers: [],
      drawnLayers: null, 
      heatLayer: null, 
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
    // custom buttons for map components
    clearAllLayers() {
      // remove filter areas
      this.clearFilterLayer();

      // remove STAC layers
      // TODO think of better way to store stac items and layers
      this.clearSTACLayers();
      this.stacCollectionLayers = [];

      // remove heatmap layer
      if (this.heatLayer !== null) {
        this.map.removeLayer(this.heatLayer);
      }
      this.heatLayer = null;
    }, 
    clearSTACLayers() {
      for (const layer of this.stacCollectionLayers) {
        this.map.removeLayer(layer);
      }
    }, 
    clearFilterLayer() {
      // TODO check if layers have to be removed from map as well?!
      // for (const layer of this.drawnLayers.getLayers()) {
      //   this.map.removeLayer(layer);
      // }
      this.drawnLayers.clearLayers();
      this.filterBounds = null;
    }, 
    getBoundsFromBBox(bbox) {
      return new L.LatLngBounds([bbox[0], bbox[1]], [bbox[2], bbox[3]]);
    }, 
    getLocationFilter() {
      return this.filterBounds;
    }, 
    focusMapOnLocationsList(geoBoundsList) {
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
          // TODO handle other bound types
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
      this.map.fitBounds(initialBounds);
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
      // TODO handle data structure (for later editing)

      // add intensity as third parameter in list
      // TODO use some (meaningful) weight for intensity?
      let intensityList = [];
      for (const coordinates of coordinateList) {
        const intensity = [coordinates[0], coordinates[1], 0.5];
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

    }
  },

  watch: {
    stacItems: {
      handler() {
        this.clearSTACLayers();
        for (const stac_collection_id in this.stacItems) {
          // entryList consists of all entries for a single stac collection
          const entryList = this.stacItems[stac_collection_id];
          for (const entryUID in entryList) {
            // entry consists of one single request in that stac collection
            const entry = entryList[entryUID];
            if (!entry.selected) {
              continue;
            }
            // create layer for each entry
            const newFeatureGroup = new L.FeatureGroup();
            const color = this.Utils.stringToColour(stac_collection_id);
            for (const stac_item of entry.stac_items) {
              newFeatureGroup.addLayer(L.geoJSON(stac_item));
            }
            newFeatureGroup.setStyle(
              function() {
                return {color: color}
              }
            );
            this.stacCollectionLayers.push(newFeatureGroup);
            newFeatureGroup.addTo(this.map);  
          }
        } 
      }, 
      deep: true, 
    }, 
  }, 

  mounted() {
    // build map
    const defaultFocus = [45, 20];
    const defaultZoom = 5;
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
