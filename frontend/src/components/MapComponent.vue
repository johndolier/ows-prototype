<template>
  <div class="h-full w-full mx-1 ">
    <div class="w-full my-2">
      <PButton class="inline-flex mx-2 left-button" severity="success" size="small"  label="Search Area"
        @click="selectCoordinates">
      </PButton>
      <PButton v-if="isCurrentlyDrawing" class="inline-flex mx-2 left-button" severity="danger" size="small"
        label="Abort selection" @click="abortSelection">
      </PButton>
      <!--
      <PButton v-if="!isCurrentlyDrawing" class="inline-flex mx-2 left-button" severity="warning"
        size="small" label="Clear Search" @click="clearAllLocationFilters">
      </PButton>
      -->
      <PButton class="mx-5 right-button" severity="danger" sie="small" label="Clear all" 
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

require('leaflet-draw');

import { v4 as get_uid } from 'uuid';

export default {

  name: "MapComponent",
  props: {
    documents: Object, // object that holds all documents that should eventually be displayed in the Map component
    stacItems: Object, // object that holds all stac items that have been queried + meta data if it should be displayed etc...
  },
  inject: ['Utils'],
  emits: ['addLocationFilter', 'clearAllLocationFilters'],  
  components: {},

  data() {
    return {
      map: null,
      // map layers
      stacCollectionLayers: [],
      // draw controller
      drawControl: null,
      polygonDrawer: null,
      // UI states
      isCurrentlyDrawing: false,
    }
  },

  computed: {
    mapDocuments() {
      return null;
    }, 
  },

  methods: {
    // interactive map methods
    selectCoordinates() {
      this.isCurrentlyDrawing = true;
      this.polygonDrawer.enable();
    },
    abortSelection() {
      this.polygonDrawer.disable();
      this.isCurrentlyDrawing = false;
    },
    addLocationFilterLayer(geoBounds) {
      const layer = this.createLayerFromGeoBounds(geoBounds);
      this.map.addLayer(layer);
      return layer;
    }, 
    removeFilterLayer(layer) {
      // TODO check if layer is present in map?
      this.map.removeLayer(layer);
    }, 
    clearSTACLayers() {
      for (const layer of this.stacCollectionLayers) {
        this.map.removeLayer(layer);
      }
    }, 
    clearAllLayers() {
      // loops over all layers (stac items and filter area) and removes them from map
      //console.log("clear all layers of map!");
      this.$emit('clearAllLocationFilters');
      // TODO think of better way to store stac items and layers
      this.clearSTACLayers();
      this.stacCollectionLayers = [];
    }, 
    getBoundsFromBBox(bbox) {
      return new L.LatLngBounds([bbox[0], bbox[1]], [bbox[2], bbox[3]]);
    }, 
    getBoundsFromPolygon(polygon) {
      // TODO
      console.log(polygon);
      return;
    }, 
    getBoundsFromMultiPolygon(bbox) {
      // TODO
      console.log(bbox);
      return;
    }, 
    createLayerFromGeoBounds(geoBounds) {
      const color = '#ff7800';
      if (geoBounds.type == "bbox") {
        // bbox is [south, west, north, east] 
        const bounds = this.getBoundsFromBBox(geoBounds.coords);
        const layer = new L.rectangle(bounds, {color: color});
        return layer;
      }
      else if (geoBounds.type == 'bounds') {
        const layer = new L.rectangle(geoBounds.coords, {color: color});
        return layer;
      }
      else if (geoBounds.type == 'Polygon') {
        // TODO
      }
      else if (geoBounds.type == 'MultiPolygon') {
        // TODO
      }
      // TODO implement other shapes
      console.log("warning - createLayerFromGeoInformation: unknown type (" + geoBounds.type + ")");
    }, 
    focusMap(geoBoundsList) {
      // focus map by using the center of the geobounds list
      let initialBounds = null;
      for (const geoBounds of geoBoundsList) {
        // convert 
        let currentBounds = null;
        if (geoBounds.type == 'bbox') {
          currentBounds = this.getBoundsFromBBox(geoBounds.coords);
        }
        else {
          // TODO handle other bound types
          console.log("not implemented (focusMap");
          continue;
        }
        if (initialBounds == null) {
          initialBounds = currentBounds;
        }
        else {
          console.log(initialBounds);
          initialBounds = initialBounds.extend(currentBounds);
        }
      }
      if (initialBounds == null) {
        // TODO could not compute bounds 
        return;
      }
      console.log(initialBounds);

      this.map.fitBounds(initialBounds);
    }, 

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
    this.map = L.map("mapContainer", { drawControl: false }).setView([45, 20], 5);

    L.tileLayer("http://{s}.tile.osm.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(this.map);

    let drawnItems = new L.FeatureGroup();
    this.map.addLayer(drawnItems);
    this.drawControl = new L.Control.Draw({
      edit: {
        featureGroup: drawnItems
      }
    });
    // create polygon drawer
    this.polygonDrawer = new L.Draw.Polygon(this.map);

    this.map.on('draw:created', e => {

      // TODO enable polygon (currently just bbox is allowed)
      this.isCurrentlyDrawing = false;

      /*const bbox = [
        bounds.getSouth(),
        bounds.getWest(), 
        bounds.getNorth(), 
        bounds.getEast(), 
      ]*/
      const id = get_uid();
      const geoBounds = {
        'type': 'bounds', 
        'coords':  e.layer.getBounds(), 
      };
      this.$emit('addLocationFilter', id, geoBounds);
    });
  },

  onBeforeUnmount() {
    if (this.map) {
      this.map.remove();
    }
  },
};

</script>
