# eclipse_planner
Find the perfect spot with the best window of annularity for the upcoming 2023 eclipse 

## Download and Setup Instructions

1. Click on the following link to download the required file:
2.   2023 Eclipse: [Download 2023eclipse_shapefiles.zip](https://svs.gsfc.nasa.gov/vis/a000000/a005000/a005073/2023eclipse_shapefiles.zip)
3.   2024 Eclipse: [Download 2024eclipse_shapefiles.zip](https://svs.gsfc.nasa.gov/vis/a000000/a005000/a005073/2024eclipse_shapefiles.zip) 
4. Once downloaded, unzip the file.
5. Move the unzipped files to the `data` directory in your project folder.

After completing the above steps, you should be ready to run the project. Its important to note that the duration displayed on the map is **For Annularity Only** the eclipse will actually last much longer in a given area. 


## Running the Code

To track the eclipse based on a given location, use the script provided in the project. The `separation_degrees` variable will control how much of sun coverage for annularity, closer to 0 is full coverage (not possible with an annular eclipse, but close to 0) currently set to `0.01`.

```
python eclipse_tracker.py "Your Location Name"
```

![Map Image](eclipse_plan.png)
