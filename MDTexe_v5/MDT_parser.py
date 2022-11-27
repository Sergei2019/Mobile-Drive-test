import json
import re

from const.const import RSRP, RSRQ


class MdtParser:

    def band_finder(self, letter):
        return '2600' if letter == 'N' else '1800' if letter == 'K' else '800'

    def get_enb_cid(self, file):
        lines = file.readlines()
        enb_id, cid, band = None, None, None
        for i in range(len(lines)):
            if 'network_element' in lines[i]:
                network_element_list = lines[i].split(' ')
                try:
                    cell_name_lst = network_element_list[2].split('=')
                    cell_name = network_element_list[1].split('=')[1]
                    letter = re.findall(r'\D', cell_name)[1]
                    enb_id_lst = cell_name_lst[1].split('/')
                    enb_id = int(enb_id_lst[2].split('-')[1])
                    cell_id = enb_id_lst[3].split('-')[1]
                    cid = int(cell_id[0:len(cell_id)-1])
                    band = self.band_finder(letter)
                except IndexError:
                    pass
                return enb_id, cid, band

    def bin_to_dec(self, num):
        dec_int = int(num, 2)
        enb_id = dec_int//256
        cell_id = dec_int - enb_id*256
        return enb_id, cell_id

    def coords_converter(self, bin_val):
        bin_val_str = str(bin_val)
        lat = bin_val_str[2:25]
        lon = bin_val_str[26:50]
        latitude = (int(lat, 2)*90)/(2**23)
        longitude = (int(lon, 2)*360)/(2**25)
        return latitude, longitude

    def get_el_kpi(self, el, kpi):
        for kpi_pos in kpi:
            if kpi_pos.range_min <= el < kpi_pos.range_max:
                return kpi_pos.color
        raise KeyError(
            f"{el} не попадает ни под один из диапазонов kpi {kpi[0].name}"
        )

    def cdata_parser(self, file):
        cell_id, enb_id, c_rnti, rsrp, rsrq, lat, lon = (), (), (), (), (), (), ()
        lines = file.read()
        result = lines.split('<lte_message')
        result_locat = ()
        result_locat_final = ()
        for j in range(len(result)):
            if '<locationInfo-r10>' in result[j]:
                result_locat = result_locat + (result[j],)
        for el in result_locat:
            lst = el.split('<locationInfo-r10>')
            for e in lst:
                if '<ellipsoidPointWith' in e and (len(e.split('<cellIdentity>')) == 2) or ('<locationInfo' in e and 'c_rnti' in e):
                    result_locat_final = result_locat_final + (e,)
        for j in range(len(result_locat_final)):
            lines = result_locat_final[j].splitlines()
            for i in range(len(lines)):
                if 'c_rnti' in lines[i]:
                    crnti_lst = lines[i].split(' ')
                    crntilst = crnti_lst[11].split('=')
                    crnti_val = crntilst[1]
                    c_rnti = c_rnti + (crnti_val,)
                if '<ellipsoidPointWith' in lines[i]:
                    gps = int("".join(lines[i+1].split()), base=16)
                    bin_value = bin(gps)
                    lat = lat + (self.coords_converter(bin_value)[0],)
                    lon = lon + (self.coords_converter(bin_value)[1],)
                if '<cellIdentity>' in lines[i]:
                    enb_id = enb_id + (self.bin_to_dec(lines[i+1])[0],)
                    cell_id = cell_id + (self.bin_to_dec(lines[i+1])[1],)
                if '<rsrpResult-r10>' in lines[i]:
                    rsrp_value = re.split(r'\W+', lines[i])
                    rsrp = rsrp + (RSRP.get(int(rsrp_value[3])),)
                if '<rsrqResult-r10>' in lines[i]:
                    rsrq_value = re.split(r'\W+', lines[i])
                    rsrq = rsrq + (RSRQ.get(int(rsrq_value[3])),)
        len_check = [list(enb_id),
                     list(cell_id),
                     list(c_rnti),
                     list(lat),
                     list(lon),
                     list(rsrp),
                     list(rsrq)]
        check = []
        for element in len_check:
            check.append(len(element))
        max_val = max(check)
        for element in len_check:
            if len(element) < max_val:
                for i in range(0, max_val-len(element)):
                    element.append(0)
        return {'enb_id': len_check[0],
                'cell_id': len_check[1],
                'c_rnti': len_check[2],
                'lat': len_check[3],
                'lng': len_check[4],
                'RSRP': len_check[5],
                'RSRQ': len_check[6]}

    def geojson_creator(self, df, cols, lon='lng', lat='lat'):
        geojson = {'type': 'FeatureCollection', 'features': []}
        for i, rows in df.iterrows():
            feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": []
                        },
                    "properties": {
                        cols: []
                        }
                    }
            feature['geometry']['coordinates'] = [rows["lng"], rows["lat"]]
            feature['properties'][cols] = [rows[cols]]
            geojson['features'].append(feature)
        return json.dumps(geojson)
