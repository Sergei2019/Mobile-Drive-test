import pathlib
import tkinter as tk
import tkinter.ttk as ttk
from json import loads
from os import listdir, path, remove

import customtkinter
import h3pandas
import pandas as pd
from branca.element import MacroElement, Template
from folium import Circle, GeoJson, GeoJsonTooltip, Map
from folium.plugins import FloatImage
from geojson import dump, load
from geopandas import GeoSeries

from color_legend import *
from MDT_parser import MdtParser
from template_legend import template_RSRP


DIR_NAME = str(pathlib.Path().resolve())
customtkinter.set_appearance_mode("light")
root = customtkinter.CTk()
macro = MacroElement()
root.title('Генерация карты покрытия в HTML')
root.geometry('800x700+50+50')
mdt = MdtParser()
all_progress= ttk.Progressbar(root, length= 150, mode= 'determinate')
all_progress.pack(pady=10)


res_dict = {11: 'h3_11',
            12: 'h3_12',
            13: 'h3_13',
            14: 'h3_14'}

v = tk.IntVar()
v.set(0) 

resolutions = [
             ("Без агрегации", 0),
             ("11", 11),
   	         ("12", 12),
    	     ("13", 13),
             ("14", 14),]

customtkinter.CTkLabel(root,
                       text="""Выберите разрешение:""",
                       justify=tk.LEFT,
                       padx=20).pack()


def status_bar(all_progress):
    count = 0
    for f in listdir(DIR_NAME):
        if f.endswith('.csv'):
            count += 1
    pb_val = 100/count
    all_progress['value'] = 0
    return all_progress, pb_val


def clearGeojson():
    for f in listdir(DIR_NAME):
        if f.endswith('.geojson'):
            remove(path.join(DIR_NAME, f))


def dataframeCreator(dir_val, f):
    file =  open(path.join(dir_val, f), 'r',encoding="utf8")
    df = pd.DataFrame(mdt.cdata_parser(file))
    file.close()
    file = open(path.join(dir_val, f), 'r',encoding="utf8")
    enbid, cellid, band = mdt.get_enb_cid(file)
    df = df.loc[(df['enb_id'] == enbid)&(df['cell_id'] == cellid)]
    return df, enbid, cellid, band


def folium_map_create(path_to_json):
    with open(path_to_json, encoding="utf8") as file:
        gj_file = load(file)
        lon0 = gj_file['features'][len(gj_file['features'])//2]['geometry']['coordinates'][0]
        lat0 = gj_file['features'][len(gj_file['features'])//2]['geometry']['coordinates'][1]
        map_object = Map(location=[lat0, lon0], zoom_start=17)
    return map_object, gj_file


def geojsonOnMap(map_object, geodataframe, kpi_col_name, kpi):
    for _, r in geodataframe.iterrows():
        sim_geo = GeoSeries(r['geometry'])
        geo_j = sim_geo.to_json()
        geo = loads(geo_j)
        geo['features'][0]['properties'] = {
                                    'weight': 0.1,
                                    'fillColor':mdt.get_el_kpi(r[kpi_col_name], kpi),
                                    'color':mdt.get_el_kpi(r[kpi_col_name], kpi),
                                    'fillOpacity': 0.5,
                                    kpi_col_name: int(r[kpi_col_name])
                                    }
        geo_j = GeoJson(geo, 
                        lambda x : x['properties'],
                        tooltip = GeoJsonTooltip([kpi_col_name],
                        labels=False)).add_to(map_object)


def band_points(df, band, kpi_col_name, kpi):
    path_json_new = path.join(DIR_NAME, f'{kpi_col_name}_{band}.geojson')
    json_file_new = open(path_json_new, "w", encoding="utf8")
    json_file_new.write(mdt.geojson_creator(df,f'{kpi_col_name}'))
    json_file_new.close()
    with open(path_json_new, encoding="utf8") as file:
        gj = load(file)
        try:
            lon0 = gj['features'][len(gj['features'])//2]['geometry']['coordinates'][0]
            lat0 = gj['features'][len(gj['features'])//2]['geometry']['coordinates'][1]
            m = Map(location=[lat0, lon0], zoom_start=17)
            for i in range(len(gj['features'])):
                kpi_val = gj['features'][i]['properties'][f'{kpi_col_name}'][0]
                Circle( location=(gj['features'][i]['geometry']['coordinates'][1], gj['features'][i]['geometry']['coordinates'][0],),
                        radius = 2,
                        fill_color=mdt.get_el_kpi(kpi_val, kpi),
                        fill_opacity=0.9,
                        color=mdt.get_el_kpi(kpi_val, kpi), 
                        tooltip = str(kpi_val),).add_to(m) 
            m.save(f'index_{kpi_col_name}_{band}.html')
        except IndexError:
            pass


def aggrcallback(res):
    lst1 = []
    progress = status_bar(all_progress)[0]
    
    for f in listdir(DIR_NAME):
        if f.endswith('.csv'):
            root.update_idletasks()
            df, enbid, cellid, band = dataframeCreator(DIR_NAME, f)
            progress['value']+=status_bar(all_progress)[1]
            lst1.append(df)
    df1 = pd.concat(lst1)
    path_json_new = path.join(DIR_NAME, 'RSRP.geojson')
    with open(path_json_new, "w", encoding="utf8") as json_file_new:
        json_file_new.write(mdt.geojson_creator(df1,'RSRP'))
    if res != 0:
        m = folium_map_create(path_json_new)[0]
        df1 = df1.h3.geo_to_h3(res)
        df1 = df1.drop(columns=['lng', 'lat','enb_id','cell_id', 'RSRQ']).groupby(res_dict[res]).mean()
        gdf = df1.h3.h3_to_geo_boundary()
        geojsonOnMap(m, gdf, 'RSRP', RSRP_)
        macro._template = Template(template_RSRP)
        macro.add_to(m)
        m.save(f'index_.html')
        # btn_all.config(state='disabled')
        # btall_val.set('Success!')
        btn_all.configure(state='disabled')
        btall_val.set('Success!')
    else:
        m = folium_map_create(path_json_new)[0]
        gj = folium_map_create(path_json_new)[1]
        for i in range(len(gj['features'])):
            rsrp = gj['features'][i]['properties']['RSRP'][0]
            Circle( location=(gj['features'][i]['geometry']['coordinates'][1], gj['features'][i]['geometry']['coordinates'][0],),
                    radius = 3,
                    fill_color=mdt.get_el_kpi(rsrp, RSRP_),
                    fill_opacity=0.9,
                    color=mdt.get_el_kpi(rsrp, RSRP_), 
                    tooltip = str(rsrp)).add_to(m)
        macro._template = Template(template_RSRP)
        macro.add_to(m)
        m.save(f'index_all.html')
        # btn_all.config(state='disabled')
        # btall_val.set('Success!')
        btn_all.configure(state='disabled')
        btall_val.set('Success!')
    clearGeojson()


def bandcallback(res):
    progress = status_bar(all_progress)[0]
    lst1 = []
    gdf_list = []
    for f in listdir(DIR_NAME):
        if f.endswith('.csv'):
            root.update_idletasks()
            df, enbid, cellid, band = dataframeCreator(DIR_NAME, f)
            progress['value']+=status_bar(all_progress)[1]
            df['band'] = band
            lst1.append(df)
    df1 = pd.concat(lst1)
    df_800 = df1.loc[(df1['band'] == '800')]
    df_1800 = df1.loc[(df1['band'] == '1800')] 
    df_2600 = df1.loc[(df1['band'] == '2600')] 
    if res == 0:
        band_points(df_800, '800', 'RSRP', RSRP_)
        band_points(df_1800, '1800', 'RSRP', RSRP_)
        band_points(df_2600, '2600', 'RSRP', RSRP_)
    else:
        df_800 = df_800.h3.geo_to_h3(res)
        df_800 = df_800.drop(columns=['lng', 'lat','enb_id','cell_id', 'RSRQ']).groupby(res_dict[res]).mean()
        df_1800 = df_1800.h3.geo_to_h3(res)
        df_1800 = df_1800.drop(columns=['lng', 'lat','enb_id','cell_id', 'RSRQ']).groupby(res_dict[res]).mean()
        df_2600 = df_2600.h3.geo_to_h3(res)
        df_2600 = df_2600.drop(columns=['lng', 'lat','enb_id','cell_id', 'RSRQ']).groupby(res_dict[res]).mean()
        gdf_dict = {'800': df_800, '1800': df_1800, '2600': df_2600}
        for k, v in gdf_dict.items():
            gdf = v.h3.h3_to_geo_boundary()
            m = Map(location = [df1['lat'].head(1), df1['lng'].head(1)], zoom_start=17)
            geojsonOnMap(m, gdf, 'RSRP', RSRP_)
            macro._template = Template(template_RSRP)
            macro.add_to(m)
            m.save(f'index_{k}.html')
    # btn_band.config(state='disabled')
    # btband_val.set('Success!')
    btn_band.configure(state='disabled')
    btband_val.set('Success!')
    clearGeojson()


def cellcallback(res):
    progress = status_bar(all_progress)[0]
    enb_id_flag, cell_id_flag, count_equal_files, df_old = None, None, 0, None
    for f in listdir(DIR_NAME):
        if f.endswith('.csv'):
            root.update_idletasks()
            df, enbid, cellid, band = dataframeCreator(DIR_NAME, f)
            progress['value']+=status_bar(all_progress)[1]
            if enbid == enb_id_flag and cellid == cell_id_flag:
                count_equal_files += 1
                path_json = path.join(DIR_NAME, f'{enbid}_{cellid}_RSRP.geojson')
                path_json_new = path.join(DIR_NAME, f'{enbid}_{cellid}_RSRP_{count_equal_files}.geojson')
                json_file_new = open(path_json_new, "w", encoding="utf8")
                json_file_new.write(mdt.geojson_creator(df,'RSRP'))
                json_file_new.close()
                json_file_new = open(path_json_new, "r", encoding="utf8")
                json_dict_new = load(json_file_new)
                json_file_new.close()
                json_file = open(path_json, "r", encoding="utf8")
                json_dict = load(json_file)
                json_file.close()
                new_json_dict = json_dict['features'] + json_dict_new['features']
                json_dict['features'] = new_json_dict
                df = pd.concat([df,df_old])
                with open(path_json, "w") as outfile:
                    dump(json_dict, outfile)
                json_file.close()
            else:
                count_equal_files = 0
                path_json = path.join(DIR_NAME, f'{enbid}_{cellid}_RSRP.geojson')
                json_file = open(path_json, "w", encoding="utf8")
                json_file.write(mdt.geojson_creator(df,'RSRP'))
                json_file.close()
            enb_id_flag, cell_id_flag, df_old = enbid, cellid, df
            with open(path_json, encoding="utf8") as f:
                gj = load(f)
                lon0 = gj['features'][len(gj['features'])//2]['geometry']['coordinates'][0]
                lat0 = gj['features'][len(gj['features'])//2]['geometry']['coordinates'][1]
                m = Map(location=[lat0, lon0], zoom_start=17)
            df = df.h3.geo_to_h3(res)
            df = df.drop(columns=['lng', 'lat','enb_id','cell_id', 'RSRQ']).groupby(res_dict[res]).mean()
            gdf = df.h3.h3_to_geo_boundary()
            geojsonOnMap(m, gdf, 'RSRP', RSRP_)
            macro._template = Template(template_RSRP)
            macro.add_to(m)
            m.save(f'{enbid}_{cellid}.html')
    # btn_cell.config(state='disabled')
    # btcell_val.set('Success!')
    btn_cell.configure(state='disabled')
    btcell_val.set('Success!')
    clearGeojson()


def measurementsByCell(res):
    progress = status_bar(all_progress)[0]
    enb_id_flag, cell_id_flag, count_equal_files, df_old = None, None, 0, None
    for f in listdir(DIR_NAME):
        if f.endswith('.csv'):
            root.update_idletasks()
            df, enbid, cellid, band = dataframeCreator(DIR_NAME, f)
            progress['value']+=status_bar(all_progress)[1]
            if enbid == enb_id_flag and cellid == cell_id_flag:
                path_json = path.join(DIR_NAME, f'{enbid}_{cellid}_meas.geojson')
                path_json_new = path.join(DIR_NAME, f'{enbid}_{cellid}_meas_{count_equal_files}.geojson')
                json_file_new = open(path_json_new, "w", encoding="utf8")
                json_file_new.write(mdt.geojson_creator(df,'c_rnti'))
                json_file_new.close()
                json_file_new = open(path_json_new, "r", encoding="utf8")
                json_dict_new = load(json_file_new)
                json_file_new.close()
                json_file = open(path_json, "r", encoding="utf8")
                json_dict = load(json_file)
                json_file.close()
                new_json_dict = json_dict['features'] + json_dict_new['features']
                json_dict['features'] = new_json_dict
                df = pd.concat([df,df_old])
                with open(path_json, "w") as outfile:
                    dump(json_dict, outfile)
                json_file.close()
            else:
                count_equal_files = 0
                path_json = path.join(DIR_NAME, f'{enbid}_{cellid}_meas.geojson')
                json_file = open(path_json, "w", encoding="utf8")
                json_file.write(mdt.geojson_creator(df,'c_rnti'))
                json_file.close()
            enb_id_flag, cell_id_flag, df_old = enbid, cellid, df
            with open(path_json, encoding="utf8") as f:
                gj = load(f)
                lon0 = gj['features'][len(gj['features'])//2]['geometry']['coordinates'][0]
                lat0 = gj['features'][len(gj['features'])//2]['geometry']['coordinates'][1]
            m = Map(location=[lat0, lon0], zoom_start=17)
            df = df.h3.geo_to_h3(res)
            df = df.drop(columns=['lng', 'lat','enb_id','cell_id', 'RSRQ', 'RSRP']).groupby(res_dict[res]).count()
            gdf = df.h3.h3_to_geo_boundary()
            geojsonOnMap(m, gdf, 'c_rnti', MEAS_BP)
            m.save(f'{enbid}_{cellid}_meas.html')        
    # meas_cell.config(state='disabled')
    # meas_cell_val.set('Success!')
    meas_cell.configure(state='disabled')
    meas_cell_val.set('Success!')
    clearGeojson()


def runAll(res):
    aggrcallback(res)
    bandcallback(res)
    cellcallback(res)
    measurementsByCell(res)
    clearGeojson()
    btn_run_all.configure(state='disabled')
    btn_run_all_val.set('Success!')

def ShowChoice():
    return v.get()


for res, val in resolutions:
    customtkinter.CTkRadioButton(root, 
                   text=res,
                   padx = 10, 
                   variable=v, 
                   hover=True,
                   command=ShowChoice,
                   value=val).pack(anchor=tk.W)

btn_all = customtkinter.CTkButton(width=250, text ="HTML агрегированного покрытия", command = lambda: aggrcallback(v.get()))
btn_band = customtkinter.CTkButton(width=250, text ="HTML покрытия по диапазонам", command = lambda: bandcallback(v.get()))
btn_cell = customtkinter.CTkButton(width=250, text ="HTML покрытия по сотам", command = lambda: cellcallback(v.get()))
meas_cell = customtkinter.CTkButton(width=250, text ="Распределение абонентов в соте", command = lambda: measurementsByCell(v.get()))
btn_run_all = customtkinter.CTkButton(width=250, text ="Выгрузить всё", command = lambda: runAll(v.get()))
btall_val = tk.StringVar()
btband_val = tk.StringVar()
btcell_val = tk.StringVar()
meas_cell_val = tk.StringVar()
btn_run_all_val = tk.StringVar()

label_for_all = customtkinter.CTkLabel(root, textvariable = btall_val).pack()
label_for_band = customtkinter.CTkLabel(root, textvariable = btband_val).pack()
label_for_cell = customtkinter.CTkLabel(root, textvariable = btcell_val).pack()
label_for_cell_meas = customtkinter.CTkLabel(root, textvariable = meas_cell_val).pack()
label_for_run_all = customtkinter.CTkLabel(root, textvariable = btn_run_all_val).pack()
btn_all.pack(pady=10)
btn_band.pack(pady=10)
btn_cell.pack(pady=10)
meas_cell.pack(pady=10)
btn_run_all.pack(pady=10)
root.mainloop()


