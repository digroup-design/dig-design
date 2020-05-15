import gdal, time, os
import simplejson as json

def translate_geometry(geometry:dict, dest_format:str, dest_filename:str=None):
    if dest_filename is None:
        dest_filename = str(int(round(time.time() * 100000))) + ".txt"
    gdal.VectorTranslate(dest_filename, json.dumps(geometry), format=dest_format)
    with open(dest_filename, 'r') as file:
        out_data = file.read()
    os.remove(dest_filename)
    return out_data