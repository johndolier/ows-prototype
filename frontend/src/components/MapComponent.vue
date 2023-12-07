<template>
  <div class="h-full w-full mx-1 ">
    <div class="w-full my-2">
      <PButton class="inline-flex mx-2 left-button" severity="info" size="small" label="SHOW GEOTWEETS"
        @click="requestGeotweets">
      </PButton>
      <PButton class="mx-5 w-2 right-button" severity="danger" size="small" icon="pi pi-trash" label="CLEAR MAP" 
        @click="clearAllLayers">
      </PButton>
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
      // draw controller
      drawControl: null,
      // polygonDrawer: null,
      drawnLayers: null, 
      filterBounds: null, 
    }
  },

  methods: {
    // custom buttons for map components
    clearAllLayers() {
      // remove filter areas
      this.clearFilterLayer();

      // remove STAC layers
      // TODO think of better way to store stac items and layers
      this.clearSTACLayers();
      this.stacCollectionLayers = [];
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
      for (const tweet of geotweets) {
        // geojsonLayer.addData(tweet);
        tweetLatLongList.push(tweet.geometry.coordinates);
      }
      this.addHeatMap(tweetLatLongList);
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
      L.heatLayer(
        intensityList, 
        {
          maxZoom: 3,
          radius: 12, 
          //gradient: {0.4: 'blue', 0.65: 'lime', 1: 'red'}, 
          minOpacity: 0.3, 
        }
        ).addTo(this.map);
    }
  },

  watch: {
    stacItems: {
      handler() {
        this.clearSTACLayers();
        for (const [stac_collection_id, entryList] of Object.entries(this.stacItems)) {
          for (const entry of entryList) {
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
        polygon: true, 
        polyline: false, 
        circle: false, 
        rectangle: true, 
        marker: false, 
        circlemarker: false, 
      }, 
      edit: {
        featureGroup: this.drawnLayers
      }
    });
    this.map.addControl(this.drawControl);

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
