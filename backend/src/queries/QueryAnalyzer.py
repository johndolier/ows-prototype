import spacy
import json
import geocoder
import parsedatetime as pdt
from datetime import datetime, timedelta
from pytz import timezone


class QueryAnalyzer:
    # this class is used to parse geolocations and other attributes from a user query

    def __init__(self, geonames_username:str):
        self.nlp = spacy.load('en_core_web_sm')
        self.stopwords = self.nlp.Defaults.stop_words
        self.username = geonames_username

    def analyze_query(self, user_query:str):
        ''' 
            Extracts LOCATIONS, DATES and general keywords from query
            LOCATION | DATES: SPACY NAMED ENTITY RECOGNITION
            general keywords: remove location, dates and stopwords from query and return remaining words
        '''

        doc = self.nlp(user_query)
        loc_list = []
        date_list = []
        rest_str = user_query
        for ent in reversed(doc.ents):
            if ent.label_ == 'GPE':
                # location
                loc_list.append(ent.text)
                # remove word from string
                rest_str = rest_str[:ent.start_char] + rest_str[ent.end_char:]
            elif ent.label_ == 'DATE':
                # date
                date_list.append(ent.text)
                # remove word from string
                rest_str = rest_str[:ent.start_char] + rest_str[ent.end_char:]

        general_keywords = []
        for word in rest_str.split():
            if word.lower() not in self.stopwords:
                general_keywords.append(word)
        
        parsed_loc_list = self._get_location_and_geobounds_list(loc_list)
        parsed_dates_list = self._get_time_intervals(date_list)
        
        if not parsed_loc_list:
            print("(QueryAnalyzer) could not extract locations from query")
        if not parsed_dates_list:
            print("(QueryAnalyzer) could not extract dates from query")
        return {
            'locations': parsed_loc_list, # tuple list ('loc_name', 'bounds')
            'dates': parsed_dates_list, # list of datetimes ['start', 'end'] | []
            'general_keywords': general_keywords, # general keywords list
        }
         

    def _get_time_intervals(self, date_list:list[str]) -> tuple[datetime, datetime]:
        ''' this function transforms the extracted time mentions in the query into a valid datetime time range
            if no dates are provided, it returns an empty list
            otherwise, it will compute a time range accordingly 
        '''
        # TODO improve function 
        cal = pdt.Calendar()
        if len(date_list) == 0:
            # no dates present
            return []
        
        # only take first date and add one day to create range -> TODO improve this!!
        date = date_list[0]
        start_dt, valid = cal.parseDT(datetimeString=date, tzinfo=timezone("Europe/Berlin"))
        if not valid:
            return []
        
        # TODO define more meaningful range (for now, always add 1 day from start)
        end_dt = start_dt + timedelta(days=1)
        print(f"parsed date expression ({date}) into time interval (start: {start_dt}, end: {end_dt})")
        return [start_dt, end_dt]

    def _get_location_and_geobounds_list(self, loc_list:list[str]):
        ''' 
            Fetches bounding box for best match with geonames.org
            Returns a combined list of location references and bounding boxes
         '''
        if not loc_list:
            # no locations found
            return []
        
        result_list = []
        for loc in loc_list:
            try:
                # TODO add more shapes (currently only bounding boxes are supported)
                bbox = self.__get_bbox_from_location(loc)
                geobounds = {
                    'type': 'bbox', 
                    'coords': bbox
                }
            except Exception as e:
                print(e)
                geobounds = None
            
            if geobounds is None:
                print(f"warning - no bbox found for location {loc}")
                continue # query failed
                
            #print(f"bbox found for location {loc}: {bbox}")
            result_list.append((loc, geobounds))
        return result_list
    

    def __get_bbox_from_location(self, location:str):
        # first request fetches geonames id (using best single match)
        g = geocoder.geonames(location, key=self.username)
        # second call fetches details (-> bbox)
        # https://geocoder.readthedocs.io/providers/GeoNames.html
        details = geocoder.geonames(g.geonames_id, method='details', key=self.username)
        try:
            # TODO extract more data from details object? 
            # extracts coordinates from details.bbox attribute
            # returns bbox
            bbox = [
                details.bbox['southwest'][0], 
                details.bbox['southwest'][1], 
                details.bbox['northeast'][0], 
                details.bbox['northeast'][1], 
            ]
            return bbox
        except Exception as e:
            print(e)




