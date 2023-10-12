
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
from shapely.geometry import Point
import gps
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

from shapely.geometry import Point

def generate_map(lat, lon, center_path, annular_path, duration):
    # Convert string lat/lon values to float
    lon_float = float(lon)
    lat_float = float(lat)
    point = Point(lon_float, lat_float)
    
    # Check if the point is inside Utah
    us_states = gpd.read_file('maps/gz_2010_us_040_00_500k.json')
    utah = us_states[us_states['NAME'] == 'Utah']
    outside_utah = not utah.geometry.contains(point).any()

    # Set the figure size based on the location
    if outside_utah:
        fig, ax = plt.subplots(figsize=(15, 15))
    else:
        fig, ax = plt.subplots(figsize=(10, 10))
    
    # Plot the US states and the Utah boundary
    us_states.boundary.plot(ax=ax, linewidth=1, color="lightgrey")
    utah.boundary.plot(ax=ax, linewidth=1.5, color="lightgrey")
    
    # Plotting the annular path and center line
    center_gdf = gpd.read_file(center_path)
    annular_gdf = gpd.read_file(annular_path)
    center_gdf.boundary.plot(ax=ax, color='blue', linewidth=1, label="Eclipse Center Line")
    annular_gdf.plot(ax=ax, color='#ff0000', edgecolor='black', label="Annular Path")
    
    # Plot the location marker
    ax.scatter(lon_float, lat_float, color='green', s=100, zorder=10)
    ax.annotate(f"Your location will see {duration} of annularity",
                xy=(lon_float, lat_float), xytext=(3,3), textcoords="offset points", zorder=10)
    
    # Adjust the map's view based on the point's location
    if outside_utah:
        ax.set_xlim(-130, -65)
        ax.set_ylim(24, 50)
    else:
        shift = -0.5
        ax.set_xlim(utah.bounds.iloc[0]['minx']-1, utah.bounds.iloc[0]['maxx']+1)
        ax.set_ylim(utah.bounds.iloc[0]['miny']-1 + shift, utah.bounds.iloc[0]['maxy']+1 + shift)
    
    plt.legend()
    plt.title("Eclipse Tracking Map")
    plt.show()
    return plt





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

def get_gps_data():
    location = gps.GPS()
    return location.get_location()
    
#lat, lon = 36.9983, -110.0985
def eclipse_tracker():
    lat, lon = get_gps_data()
    # 38.3668, -110.7140 caineville
    # 38.2456, -111.2462 temple of the sun, capitol reef
    # 38.406486, -110.792295 mars desert research lab
    #lat, lon = 38.406486, -110.792295
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
        plt.savefig("plan.png")
        return m
    else:
        print("No Annular Separation in This Area.")
        draw_eclipse(min_sep[0] if min_sep else 100)
        m = generate_map(lat, lon, center_path, annular_path, "0")
        plt.savefig("plan.png")
        return m

def main():
    parser = argparse.ArgumentParser(description='Track eclipse based on location.')
    #parser.add_argument('location', type=str, help='Location for eclipse tracking (e.g. "Monument Valley, AZ").')
    args = parser.parse_args()

    eclipse_tracker()

if __name__ == "__main__":
    main()