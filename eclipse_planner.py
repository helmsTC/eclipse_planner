
import folium
import matplotlib.pyplot as plt
import numpy as np
import requests
import argparse
import webbrowser
import geopandas as gpd
from datetime import datetime, timedelta, timezone
from dateutil.parser import parse
from skyfield.api import Topos, load
from skyfield.searchlib import find_discrete
from skyfield.searchlib import find_minima
from folium import IFrame
import base64

def convert_utc_to_mdt(utc_time_str):
    utc_time = parse(utc_time_str).replace(tzinfo=timezone.utc)
    dst_start = datetime(2023, 3, 12, tzinfo=timezone.utc)
    dst_end = datetime(2023, 11, 5, tzinfo=timezone.utc)
    if dst_start <= utc_time < dst_end:
        mdt_time = utc_time - timedelta(hours=6)
        time_suffix = "MDT"
    else:
        mdt_time = utc_time - timedelta(hours=7)
        time_suffix = "MST"
    return mdt_time.strftime('%Y-%m-%dT%H:%M:%S') + f" {time_suffix}"

def embed_image_base64(img_filename):
    """Convert an image file to its base64 representation and prefix with appropriate header."""
    with open(img_filename, "rb") as image_file:
        base64_img = base64.b64encode(image_file.read()).decode("utf-8")
    return f"data:image/png;base64,{base64_img}"

def generate_map(lat, lon, center_path, annular_path, duration):
    center_gdf = gpd.read_file(center_path)
    annular_gdf = gpd.read_file(annular_path)
    m = folium.Map(location=[lat, lon], zoom_start=8)
    folium.GeoJson(center_gdf.to_json(), name="Eclipse Center Line").add_to(m)
    folium.GeoJson(annular_gdf.to_json(), name="Annular Path", style_function=lambda x: {'fillColor': '#ff0000', 'color': '#ff0000'}).add_to(m)
    
    # Embed the image as base64 into the HTML
    base64_img = embed_image_base64("eclipse_representation.png")
    html = f'<img src="{base64_img}" alt="eclipse representation" width="300" height="150">'
    
    iframe = IFrame(html, width=320, height=170)
    popup = folium.Popup(iframe, max_width=2650)
    
    folium.Marker([lat, lon], tooltip=f"Your Location will see {duration} of annularity", popup=popup).add_to(m)
    m.add_child(folium.LatLngPopup())
    folium.LayerControl().add_to(m)
    
    return m

def separation_at_time(t, location_topos, sun, moon):
    astrometric_sun = location_topos.at(t).observe(sun).apparent()
    astrometric_moon = location_topos.at(t).observe(moon).apparent()
    return astrometric_sun.separation_from(astrometric_moon).degrees

def is_eclipsed(t, location, sun, moon):
    astrometric_sun = location.at(t).observe(sun).apparent()
    astrometric_moon = location.at(t).observe(moon).apparent()
    separation_degrees = astrometric_sun.separation_from(astrometric_moon).degrees
    return separation_degrees < 0.01 # Closer to 0 = More Eclipse, change based on variation distance from the center-line path

def draw_eclipse(separation_degrees):
    fig, ax = plt.subplots()
    sun_radius, moon_radius = 1, 0.95
    sun_center = (0, 0)
    moon_center = (separation_degrees, 0)
    sun_circle = plt.Circle(sun_center, sun_radius, color='yellow')
    moon_circle = plt.Circle(moon_center, moon_radius, color='grey')
    ax.add_artist(sun_circle)
    ax.add_artist(moon_circle)
    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.5, 1.5)
    ax.set_aspect('equal', 'box')  
    ax.axis('off')  
    plt.savefig("eclipse_representation.png", bbox_inches='tight', pad_inches=0, transparent=True)

#lat, lon = 36.9983, -110.0985
def eclipse_tracker(location):
    #locatation example: "Monument Valley, AZ"
    response = requests.get(f'https://nominatim.openstreetmap.org/search?q={location}&format=json')
    data = response.json()
    lat = data[0]['lat']
    lon = data[0]['lon']
    eph = load('de421.bsp')
    ts = load.timescale()
    earth, sun, moon = eph['earth'], eph['sun'], eph['moon']
    location = earth + Topos(latitude_degrees=float(lat), longitude_degrees=float(lon))
    func = lambda time: is_eclipsed(time, location, sun, moon)
    func.rough_period = 1/24/60  # Check every minute

    start_time = ts.utc(2023, 10, 14, 13)  # 9 AM MDT
    end_time = ts.utc(2023, 10, 14, 22)    # 12 PM MDT
    
    separation_func = lambda t: separation_at_time(t, location, sun, moon)
    separation_func.rough_period = 1/24/60  # Check every 5 minutes

    min_t, min_sep = find_minima(start_time, end_time, separation_func)
    t, y = find_discrete(start_time, end_time, func)
    start = None
    end = None
    print(min_sep)
    for ti, yi in zip(t, y):
        if yi:
            start = convert_utc_to_mdt(ti.utc_iso())
            print(f"{start} Eclipse is happening")
        else:
            end = convert_utc_to_mdt(ti.utc_iso())
            print(f"{end} Eclipse ended")


    center_path = "data/center.shp" 
    annular_path = "data/upath_hi.shp"

    if start:
        start_time_obj = datetime.strptime(start, '%Y-%m-%dT%H:%M:%S MDT')
        end_time_obj = datetime.strptime(end, '%Y-%m-%dT%H:%M:%S MDT')
        duration = end_time_obj - start_time_obj
        hours, remainder = divmod(duration.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        formatted_duration = f"{minutes} minutes {seconds} seconds"
        print("Annularity will last a duration of: ", formatted_duration)  
        draw_eclipse(min_sep[0] if min_sep else 100)
        m = generate_map(lat, lon, center_path, annular_path, formatted_duration)
        m.save("Eclipse_plan.html")  
        return m
    else:
        print("No Annular Separation in This Area.")
        draw_eclipse(min_sep[0] if min_sep else 100)
        m = generate_map(lat, lon, center_path, annular_path, "0")
        m.save("Eclipse_plan.html")  
        return m

def main():
    parser = argparse.ArgumentParser(description='Track eclipse based on location.')
    parser.add_argument('location', type=str, help='Location for eclipse tracking (e.g. "Monument Valley, AZ").')
    args = parser.parse_args()

    eclipse_tracker(args.location)
    webbrowser.open("Eclipse_plan.html", new=2)

if __name__ == "__main__":
    main()