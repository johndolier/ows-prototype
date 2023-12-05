

export default class {
    stringToColour(str) {
        let hash = 0;
        str.split('').forEach(char => {
          hash = char.charCodeAt(0) + ((hash << 5) - hash)
        })
        let colour = '#'
        for (let i = 0; i < 3; i++) {
          const value = (hash >> (i * 8)) & 0xff
          colour += value.toString(16).padStart(2, '0')
        }
        return colour
      } 
    
    getBBoxFromBounds(bounds) {
      // return a list (bbox) from the Leaflet bounds object
      // TODO add type checks
      let bbox = [
        bounds.getSouth(),
        bounds.getWest(), 
        bounds.getNorth(), 
        bounds.getEast()
      ]
      return bbox;
    }
}


