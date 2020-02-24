import gmplot
import SanDiego

#TODO: Get API key to test this module
#Ref - https://www.tutorialspoint.com/plotting-google-map-using-gmplot-package-in-python
def draw_map(geometry):
    coordinates = geometry['coordinates']
    latitude_list = []
    longitude_list = []
    if geometry['type'].lower() == "polygon":
        #3d array
        for x in coordinates:
            for y in x:
                for z in y:
                    latitude_list.append(z[0])
                    longitude_list.append(z[1])
    elif geometry['type'].lower() == "multipolygon":
        for w in coordinates:
            for x in w:
                for y in x:
                    for z in y:
                        latitude_list.append(z[0])
                        longitude_list.append(z[1])
    gmap = gmplot.GoogleMapPlotter(latitude_list[0], longitude_list[0], 15)


