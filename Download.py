import os
import copernicusmarine
import geopandas as gpd
import pandas as pd
import numpy as np
import xarray as xr
from shapely.geometry import box as shp_box

#Gnereiert mit Hilfe von KI (ChatGPT 5.1, OpenAI)

###############################################################################################
#Generieren der ausschnitte für Sattelitenbilder
###############################################################################################
probenlayer="Probenstandorte_Export.gpkg"
proben = gpd.read_file(probenlayer)
proben=proben[~proben.geometry.is_empty & proben.geometry.notna()].copy()



#Version mit Reprojektion zu EPSG:3035 (Meter)
Kantenlänge=3000#m

proben_3035 = proben.to_crs(3035)
half=Kantenlänge/2
squares = proben_3035.geometry.apply(lambda p: shp_box(p.x - half, p.y - half, p.x + half, p.y + half))
boxen_3035 = gpd.GeoDataFrame(proben_3035.drop(columns="geometry"), geometry=squares, crs=proben_3035.crs)
boxen_wgs84 = boxen_3035.to_crs(4326)
boxen_wgs84.to_file("boxen.gpkg", layer="boxen", driver="GPKG")
b=boxen_wgs84.bounds
boxlist=list(zip(b.minx, b.miny, b.maxx, b.maxy))


###############################################################################################
# Export der Probnatribute
###############################################################################################


#Datum der Proben
proben['Datum [dd/mm/yyyy]'] = pd.to_datetime(proben['Datum [dd/mm/yyyy]'], format='%d.%m.%y')
datum_liste = proben['Datum [dd/mm/yyyy]'].dt.strftime('%Y-%m-%dT00:00:00').tolist()
pd.to_datetime(datum_liste[2])+pd.Timedelta(hours=23, minutes=59, seconds=59)

# Namen der Proben
probenamen=proben["Sample-Nummer"].tolist()


###############################################################################################
#Testing
###############################################################################################

if 14==len(boxlist)==len(datum_liste)==len(proben)==len(probenamen):
    test_box = 0
    for mnx, mny, mxx, mxy in boxlist:
        if (mnx < mxx) and (mny < mxy):
            test_box += 1
    if test_box == len(boxlist):
       print("Gseet sowit eigentlich guet us. Guet gmacht Jan!!!")
    else:
      print(f"du hesch bi {len(boxlist)-test_box} Boxe en Fähler drinne mach besser!")
    print("Woow stell der vor du hesch überal glich vill Element i dine Liste. Lets goooooo")
else:
  print("Vill spass bim Fähler sueche")



###############################################################################################
#Daten herunterladen
###############################################################################################

datasetsMED=["cmems_obs-oc_med_bgc-plankton_my_l4-gapfree-multi-1km_P1D",
#A   #https://data.marine.copernicus.eu/product/OCEANCOLOUR_MED_BGC_L4_MY_009_144/description
             "cmems_obs-oc_med_bgc-plankton_nrt_l4-gapfree-multi-1km_P1D",
#B   #https://data.marine.copernicus.eu/product/OCEANCOLOUR_MED_BGC_L4_NRT_009_142/description
             "cmems_obs-oc_med_bgc-plankton_my_l3-multi-1km_P1D",
#C   #https://data.marine.copernicus.eu/product/OCEANCOLOUR_MED_BGC_L3_MY_009_143/description
             "cmems_obs-oc_med_bgc-plankton_my_l3-olci-300m_P1D",      
#D   #https://data.marine.copernicus.eu/product/OCEANCOLOUR_MED_BGC_L3_MY_009_143/description
             "cmems_obs-oc_med_bgc-plankton_nrt_l3-multi-1km_P1D",
#E   #https://data.marine.copernicus.eu/product/OCEANCOLOUR_MED_BGC_L3_NRT_009_141/description
             "cmems_obs-oc_med_bgc-plankton_nrt_l3-olci-300m_P1D"
#F   #https://data.marine.copernicus.eu/product/OCEANCOLOUR_MED_BGC_L3_NRT_009_141/description
            ]
datasetnameMED=["A","B","C","D","E","F"]
if len(datasetsMED)==len(datasetnameMED):
    # datasets=["cmems_obs-oc_med_bgc-plankton_my_l4-gapfree-multi-1km_P1D"]
    download_dir="C:/Users/jan/OneDrive - ZHAW/Semester_Unterlagen/HS25/SA_2/Code/Download"
    for ds, dn in zip(datasetsMED, datasetnameMED):
        for i in range(len(proben)-2):  #Probe 13 und 14 sind ausserhalb des beriches der Satelitenmodelle        
            minlon = boxlist[i][0]
            minlat = boxlist[i][1]
            maxlon = boxlist[i][2]
            maxlat = boxlist[i][3]
            datum=datum_liste[i]
            name=probenamen[i]
            filename = f"{dn}_{name}.nc"
            out_fp = os.path.join(download_dir, filename)

            copernicusmarine.subset(
                dataset_id=ds,
                variables=["CHL"],
                minimum_longitude=minlon,
                maximum_longitude=maxlon,
                minimum_latitude=minlat,
                maximum_latitude=maxlat,
                start_datetime=datum,
                end_datetime=datum,
                output_directory="C:/Users/jan/OneDrive - ZHAW/Semester_Unterlagen/HS25/SA_2/Code/Download",
                output_filename = filename,
                skip_existing=True,
                coordinates_selection_method= "outside",
                overwrite=False
                )
else:
    print("Fäler bi de Modell und de näme. Es sind ned glich vill modell wie Näme vorhande. Mach Besser!")


###############################################################################################
# Bilder Auswerten
###############################################################################################

nc_files = sorted([f for f in os.listdir(download_dir) if f.endswith(".nc")])

file_names = []
chl_means = []
chl_sd = []
chl_min = []
chl_max = []
rows = []

for f in nc_files:
    p = os.path.join(download_dir, f)
    try:
        ds = xr.open_dataset(p)
        if "CHL" in ds.variables and ds["CHL"].size > 0:
            median_val = float(ds ["CHL"].median(skipna=True))
            mean_val = float(ds["CHL"].mean(skipna=True))
            sd_val = float(ds["CHL"].std(skipna=True))
            min_val = float(ds["CHL"].min(skipna=True))
            max_val = float(ds["CHL"].max(skipna=True))
        else:
            median_val = np.nan
            mean_val = np.nan
            sd_val = np.nan
            min_val = np.nan
            max_val = np.nan
        ds.close()
    except Exception:
        # falls Datei doch korrupt ist: sauber weiter
        mean_val = np.nan
    model, probe = f.split("_", 1)
    probe = probe.rsplit(".", 1)[0]
    rows.append({
        "filename": f,
        "model": model,
        "probe": probe,
        "median_CHL": median_val,
        "mean_CHL": mean_val,
        "sd_CHL": sd_val,
        "min_CHL": min_val,
        "max_CHL": max_val,
    })
ergebnisse= pd.DataFrame(rows)
ergebnisse.to_csv('C:/Users/jan/OneDrive - ZHAW/Semester_Unterlagen/HS25/SA_2/Code/Ergebnisse.csv')


###############################################################################################
#SICHERUNG
###############################################################################################


#unterschied
    # delta = []
    # for i in range(len(boxlist)):
    #     diff = abs(alt_boxlist[i][4] - boxlist[i][4])   # Differenz der 1. Werte
    #     delta.append(diff)



#geopandas centroides  verwen

#Version mit Buffer (alt)
    # buffer_boxen=proben.buffer(0.0125*10,cap_style="square")
    # buffer_boxen_gdf = gpd.GeoDataFrame(geometry=alt_boxen, crs=proben.crs)
    # buffer_boxen_gdf.to_file("boxen_buffer.gpkg", layer="boxen", driver="GPKG")
    # # Boxen in listen mit Tuples für unten
    # nuffer_boxlist = [(g.bounds[0], g.bounds[2], g.bounds[1], g.bounds[3])  # (min_lon, max_lon, min_lat, max_lat)
    #           for g in alt_boxen]


## Data Download 

copernicusmarine.subset(
  dataset_id="cmems_obs-oc_med_bgc-plankton_my_l4-gapfree-multi-1km_P1D",
  variables=["CHL"],
  
  start_datetime="2025-07-21T00:00:00",
  end_datetime="2025-07-21T00:00:00",
)
